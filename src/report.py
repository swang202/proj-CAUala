"""
Report builder -- renders a TargetAppraisal to JSON, Markdown, HTML, and an
8-axis CSP spider chart (inline SVG, no plotting dependency).

Follows the 12-section canonical order in the Report Spec. The HEADLINE is always
the gated composite tier; the posterior appears only via Posterior.render()
(band pre-calibration), subordinate to the tier. Every quantitative claim carries
a provenance tag. Nothing here computes a score -- it only presents what the
deterministic scorer produced.
"""

from __future__ import annotations

import html
import json
import math
from typing import Optional

from src.question import Question
from src.schema import (
    Dimension,
    Direction,
    EvidenceItem,
    TargetAppraisal,
    Tier,
)
from src.scoring_engine import RUBRIC, csp_profile

_AXES = ("A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4")


# ---------------------------------------------------------------------------
# provenance tagging
# ---------------------------------------------------------------------------


def _provenance_tag(item: EvidenceItem) -> str:
    """Every quantitative claim gets exactly one tag. Curated fixtures are
    hand-entered from papers, so an item with a source is [RETRIEVED]; a bare
    effect with no source would be [TRAINING - verify] (schema forbids that)."""
    if item.source:
        return "[RETRIEVED]"
    return "[TRAINING - verify]"


def _effect_str(item: EvidenceItem) -> str:
    e = item.effect
    if e is None:
        return "no effect size on record"
    ci = f" (95% CI {e.ci_low}-{e.ci_high})" if e.is_precise else " (no CI)"
    null = " [crosses null]" if e.is_null else ""
    return f"{e.value} {e.units}{ci}{null}"


# ---------------------------------------------------------------------------
# spider chart (inline SVG radar, 8 axes, 0..3)
# ---------------------------------------------------------------------------


def spider_svg(profile: dict[str, int], size: int = 320) -> str:
    """An accessible 8-spoke radar of the CSP profile. Self-contained SVG."""
    cx = cy = size / 2
    radius = size * 0.36
    n = len(_AXES)
    grid_color = "#c9d1d9"
    ident_color = "#2563eb"  # Family A (identification) spokes
    corr_color = "#0d9488"   # Family B (corroboration) spokes
    fill = "rgba(37,99,235,0.18)"
    stroke = "#2563eb"

    def point(i: int, value: float) -> tuple[float, float]:
        angle = -math.pi / 2 + 2 * math.pi * i / n
        r = radius * (value / 3.0)
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    parts: list[str] = [f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
                        f'role="img" aria-label="Causal Strength Profile radar">']
    # concentric grid rings at 1,2,3
    for ring in (1, 2, 3):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, ring) for i in range(n)))
        parts.append(f'<polygon points="{pts}" fill="none" stroke="{grid_color}" stroke-width="1"/>')
    # spokes + labels
    for i, axis in enumerate(_AXES):
        x, y = point(i, 3)
        color = ident_color if axis.startswith("A") else corr_color
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{grid_color}" stroke-width="1"/>')
        lx, ly = point(i, 3.5)
        anchor = "middle"
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="11" font-family="sans-serif" '
            f'fill="{color}" text-anchor="{anchor}" dominant-baseline="middle">{axis}</text>'
        )
    # data polygon
    dpts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, profile[a]) for i, a in enumerate(_AXES)))
    parts.append(f'<polygon points="{dpts}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    for i, a in enumerate(_AXES):
        x, y = point(i, profile[a])
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{stroke}"/>')
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# report data assembly
# ---------------------------------------------------------------------------


def _split_for_against(appraisal: TargetAppraisal) -> tuple[list[EvidenceItem], list[EvidenceItem]]:
    for_items: list[EvidenceItem] = []
    against_items: list[EvidenceItem] = []
    for assessment in appraisal.dimensions.values():
        for item in assessment.items:
            if item.direction == Direction.NULL or assessment.tier == Tier.CONTRADICTED:
                against_items.append(item)
            else:
                for_items.append(item)
    return for_items, against_items


def _estimand(appraisal: TargetAppraisal, q: Optional[Question]) -> dict[str, str]:
    return {
        "X (intervened on)": appraisal.target,
        "a vs b (contrast)": "perturbed vs reference level of the target",
        "M (readout)": "disease-relevant clinical outcome / endpoint",
        "system (held fixed)": appraisal.context.describe(),
        "population": appraisal.context.ancestry or "unspecified (flagged: generalization not assumed)",
    }


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def to_markdown(appraisal: TargetAppraisal, q: Optional[Question] = None) -> str:
    profile = csp_profile(appraisal.dimensions)
    min_ident = min(profile[a] for a in ("A1", "A2", "A3", "A4"))
    gate = RUBRIC["identification_gate"][min_ident]
    for_items, against_items = _split_for_against(appraisal)
    L: list[str] = []

    L.append(f"# Causal evidence appraisal — {appraisal.target} → {appraisal.disease}\n")

    # 1. Verdict (BLUF)
    L.append("## 1. Verdict (BLUF)\n")
    L.append(f"**Headline tier: `{appraisal.composite.value}`** — the gated ordinal verdict.\n")
    L.append(f"- **Structural position:** `{appraisal.archetype.value}`")
    L.append(f"- **Necessity × sufficiency:** `{appraisal.inus.box.value}` — {appraisal.inus.therapeutic_note}")
    L.append(f"- **Scope:** {appraisal.context.describe()}")
    conf = appraisal.posterior.render() if appraisal.posterior else "confidence not scored"
    L.append(f"- **Subordinate confidence:** {conf} *(never exceeds the tier; digits shown only once calibrated)*")
    L.append(f"\n> {appraisal.archetype_rationale}\n")
    L.append(f"**One-line:** {appraisal.verdict_line()}\n")

    # 2. Estimand
    L.append("## 2. Causal question & estimand\n")
    L.append("Effect = M( system | do(X=a) ) − M( system | do(X=b) ), five slots filled:\n")
    for slot, val in _estimand(appraisal, q).items():
        L.append(f"- **{slot}:** {val}")
    L.append("")

    # 3. DAG (in words)
    L.append("## 3. Causal DAG (adjustment set in words)\n")
    L.append(f"- **Exposure X:** {appraisal.target} · **Outcome Y:** {appraisal.disease}")
    L.append("- **Instrument:** germline genotype (fixes direction; used by MR / genetic arms).")
    L.append("- **Adjustment set (back-door):** condition on shared common causes of X and Y "
             "(e.g. age, ancestry principal components); **do NOT** condition on downstream "
             "mediators or post-onset measurements.")
    L.append("- **Collider (do NOT adjust):** any selection node (survivorship in post-mortem "
             "cohorts, cell-line selection) — conditioning on it induces bias.")
    L.append("")

    # 4. Four-explanation checklist
    L.append("## 4. Four-explanation checklist\n")
    L.append("| # | Explanation | Design that addresses it | Status here |")
    L.append("|---|---|---|---|")
    gen = appraisal.dimensions.get(Dimension.GENETIC)
    temporal = appraisal.dimensions.get(Dimension.TEMPORAL)
    x_to_y = "supported" if appraisal.composite.value in ("causal_driver", "likely_causal") else "open"
    rev = "addressed (genotype fixed at conception)" if gen else "open"
    L.append(f"| 1 | X → Y (causal) | MR + coloc; isogenic KI/rescue | {x_to_y} |")
    L.append(f"| 2 | Y → X (reverse) | instrument fixed at conception; longitudinal | {rev} |")
    L.append("| 3 | Z → X, Z → Y (confound) | randomized / MR; conditional KO | "
             + ("addressed by genetic randomization" if gen else "open") + " |")
    L.append("| 4 | X → S ← Y (collider) | population sampling; IPW | "
             + ("modeled" if temporal else "acknowledged, not fully modeled") + " |")
    L.append("")

    # 5. Evidence FOR
    L.append("## 5. Evidence FOR\n")
    if for_items:
        for it in for_items:
            L.append(f"- {_provenance_tag(it)} **{it.evidence_type.value}** ({it.dimension.value}, "
                     f"{it.direction.value}): {_effect_str(it)} — `{it.source}` "
                     f"[{it.system.value}/{it.readout.value}]")
            if it.assumptions_required:
                L.append(f"    - load-bearing assumption(s): {', '.join(a.value for a in it.assumptions_required)}")
    else:
        L.append("- None on record.")
    L.append("")

    # 6. Evidence AGAINST / nulls
    L.append("## 6. Evidence AGAINST / informative nulls\n")
    if against_items:
        for it in against_items:
            L.append(f"- {_provenance_tag(it)} **{it.evidence_type.value}** ({it.dimension.value}, "
                     f"{it.direction.value}): {_effect_str(it)} — `{it.source}`")
            if it.notes:
                L.append(f"    - {it.notes}")
    else:
        L.append("- No informative nulls on record.")
    L.append("")

    # 7. CSP profile
    L.append("## 7. Causal Strength Profile (CSP)\n")
    L.append(f"Identification gate: min(A1..A4) = **{min_ident}** → gated tier **{gate['tier']}** "
             f"({gate['meaning']}). Corroboration (B-axes) cannot lift this ceiling.\n")
    L.append("| Axis | Score (0–3) | Family |")
    L.append("|---|---|---|")
    for a in _AXES:
        fam = "identification" if a.startswith("A") else "corroboration"
        L.append(f"| {a} {RUBRIC['axes'][a]['name']} | {profile[a]} | {fam} |")
    L.append("")

    # 8. Evidence hierarchy
    L.append("## 8. Evidence hierarchy (by dimension tier)\n")
    L.append("| Dimension | Tier | # items |")
    L.append("|---|---|---|")
    for d, a in sorted(appraisal.dimensions.items(), key=lambda kv: kv[0].value):
        L.append(f"| {d.value} | {a.tier.value} | {len(a.items)} |")
    L.append("")

    # 9. Databases -> named gaps
    L.append("## 9. Data & databases → named gaps\n")
    if appraisal.not_examined:
        for d in appraisal.not_examined:
            L.append(f"- **Gap — {d.value}:** not queried in this run. {appraisal.stopped_because or ''}")
    else:
        L.append("- No unexamined causal dimensions for this arrow.")
    L.append("")

    # 10. Roadmap
    L.append("## 10. Experimental roadmap\n")
    L.append(f"- **Next experiment (weakest, most cheaply strengthened):** {appraisal.next_experiment}")
    L.append("")

    # 11. Conclusions by tier
    L.append("## 11. Conclusions\n")
    if appraisal.conflicts:
        L.append("**Conflicts (surfaced, never averaged):**")
        for c in appraisal.conflicts:
            L.append(f"- {c}")
    if appraisal.coarse_label_warning:
        L.append("- ⚠️ Coarse disease label: stratification advised.")
    L.append("\n**Known limitations:**")
    for lim in appraisal.known_limitations:
        L.append(f"- {lim}")
    L.append("")

    # 12. References
    L.append("## 12. References\n")
    seen = {}
    for a in appraisal.dimensions.values():
        for it in a.items:
            seen.setdefault(it.source, it.provenance_group)
    for src, grp in seen.items():
        L.append(f"- `{src}` — provenance group `{grp}` [unverified: curated placeholder, verify in-source]")
    L.append("")

    return "\n".join(L)


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------


def to_html(appraisal: TargetAppraisal, q: Optional[Question] = None) -> str:
    profile = csp_profile(appraisal.dimensions)
    svg = spider_svg(profile)
    body_md = to_markdown(appraisal, q)
    # Minimal markdown-ish -> HTML: escape, keep headings/lists/tables readable in <pre>.
    esc = html.escape(body_md)
    tier = appraisal.composite.value
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CAUala — {html.escape(appraisal.target)} → {html.escape(appraisal.disease)}</title>
<style>
 body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 900px; margin: 2rem auto;
        padding: 0 1rem; line-height: 1.5; color: #1a1a1a; }}
 .headline {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 1rem 1.25rem; }}
 .tier {{ font-size: 1.4rem; font-weight: 700; color: #1e3a8a; }}
 .chart {{ text-align: center; margin: 1.5rem 0; }}
 pre {{ white-space: pre-wrap; word-wrap: break-word; background: #f8fafc; padding: 1rem;
        border-radius: 8px; overflow-x: auto; font-size: 13px; }}
 .legend span {{ display: inline-block; margin-right: 1rem; font-size: 12px; }}
 .a {{ color: #2563eb; }} .b {{ color: #0d9488; }}
</style></head><body>
<div class="headline">
  <div class="tier">Tier: {html.escape(tier)}</div>
  <div>Position: <b>{html.escape(appraisal.archetype.value)}</b> ·
       INUS: <b>{html.escape(appraisal.inus.box.value)}</b> ·
       Scope: {html.escape(appraisal.context.describe())}</div>
  <div>Confidence: {html.escape(appraisal.posterior.render() if appraisal.posterior else 'not scored')}</div>
</div>
<div class="chart">{svg}
  <div class="legend"><span class="a">A1–A4 identification (the gate)</span>
       <span class="b">B1–B4 corroboration</span></div>
</div>
<pre>{esc}</pre>
</body></html>"""


def to_json(appraisal: TargetAppraisal) -> str:
    payload = json.loads(appraisal.model_dump_json())
    payload["csp_profile"] = csp_profile(appraisal.dimensions)
    payload["verdict_line"] = appraisal.verdict_line()
    return json.dumps(payload, indent=2)
