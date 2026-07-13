"""
Report builder -- renders a TargetAppraisal to JSON, Markdown, and a designed,
self-contained HTML report (with an 8-axis CSP spider chart, dimension tier bars,
plain-English concept explainers, and a "data sources & how they were analyzed"
section). No plotting dependency; charts are inline SVG/HTML.

Follows the 12-section canonical order in the Report Spec. The HEADLINE is always
the gated composite tier; the posterior appears only via Posterior.render()
(a band pre-calibration), subordinate to the tier. Every quantitative claim
carries a provenance tag. Nothing here computes a score -- it only presents what
the deterministic scorer produced.

Colors come from the validated data-viz reference palette (light/dark selected),
driven by CSS custom properties so the report adapts to the viewer's theme.
"""

from __future__ import annotations

import html
import json
import math
from typing import Optional

from src.provenance import cite, is_live, source_of, validation_banner
from src.question import Question
from src.schema import (
    Dimension,
    Direction,
    DimensionAssessment,
    EvidenceItem,
    TargetAppraisal,
    Tier,
)
from src.scoring_engine import RUBRIC, csp_profile

_AXES = ("A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4")

# ---------------------------------------------------------------------------
# plain-English lookups (what makes the report understandable)
# ---------------------------------------------------------------------------

_TIER_ORDER = [
    "causal_driver", "likely_causal", "plausible",
    "unvalidated", "likely_noncausal", "refuted",
]
_TIER_STATUS = {
    "causal_driver": "good", "likely_causal": "good", "plausible": "warning",
    "unvalidated": "muted", "likely_noncausal": "serious", "refuted": "critical",
}
_TIER_LABEL = {
    "causal_driver": "Causal driver", "likely_causal": "Likely causal",
    "plausible": "Plausible", "unvalidated": "Unvalidated",
    "likely_noncausal": "Likely non-causal", "refuted": "Refuted",
}
_TIER_MEANING = {
    "causal_driver": "Converging causal evidence — bidirectional genetics plus a successful "
    "human intervention. This behaves like a genuine driver you can act on.",
    "likely_causal": "Strong causal evidence on at least one axis, though short of the full "
    "bidirectional-plus-intervention convergence. Probably causal.",
    "plausible": "Some causal signal, but only moderate or indirect so far. Worth pursuing; "
    "not yet established.",
    "unvalidated": "Association and/or mechanism only — no causal-tier evidence has been brought "
    "yet. This is “untested”, not “disproven”.",
    "likely_noncausal": "The causal tests that exist point away from causation. Probably not a driver.",
    "refuted": "A causal test was performed and failed (a trial, or clean genetics pointing the "
    "other way). The causal hypothesis is contradicted.",
}
_ARCHETYPE_MEANING = {
    "validated_driver": "A validated driver: loss- and gain-of-function point opposite ways and a "
    "human intervention worked.",
    "associated_noncausal": "A marker — it tracks the disease but sits on no causal path. Real "
    "correlation, no causation.",
    "displaced_signal": "The correlation is real, but the causal signal lives one node upstream in "
    "the same pathway. You would be targeting the reporter, not the source.",
    "upstream_initiator": "An early, upstream cause. Its weak concurrent correlation is the "
    "signature of an initiator — not evidence against it.",
    "downstream_mediator": "On the causal path but downstream: an excellent biomarker, a more "
    "uncertain target. (A mediator is still causal.)",
    "reactive_consequence": "Changes only after onset — it cannot be driving what comes before it.",
    "untested": "Only a mechanism or association story on record — evidence of nothing, not "
    "evidence against.",
}
_DIM_EXPLAIN = {
    "intervention": "Did anyone actually perturb the target and watch the outcome? The strongest kind of evidence.",
    "genetic": "Does nature's randomization — genetics — support it? The arrow points away from fixed genotype.",
    "temporal": "Does the target change before the disease, not after?",
    "mediation": "Is it a driver, a mediator on the path, or downstream?",
    "mechanism": "Is there a pathway story? Plausibility only — it can never raise the score by itself.",
    "association": "The honest baseline: how strongly does it correlate? Shown separately; it never drives the verdict.",
    "robustness": "How fragile are the assumptions, and does contradictory evidence exist?",
}
_DIM_TIER_STATUS = {
    "strong": "good", "moderate": "blue", "weak": "warning",
    "absent": "muted", "contradicted": "critical",
}
_DIM_TIER_RANK = {"strong": 3, "moderate": 2, "weak": 1, "absent": 0, "contradicted": 3}
_DIRECTION_PLAIN = {
    "target_up_disease_up": "↑ target ⇒ ↑ disease (harmful)",
    "target_down_disease_down": "↓ target ⇒ ↓ disease (protective)",
    "target_up_disease_down": "↑ target ⇒ ↓ disease (protective)",
    "target_down_disease_up": "↓ target ⇒ ↑ disease (harmful)",
    "null": "no directional effect (null result)",
}


def _status_var(status: str) -> str:
    """Vivid color — for fills, marks, borders, bar fills."""
    return f"var(--{status})"


def _status_text(status: str) -> str:
    """Text-safe color — for colored WORDS, readable on both surfaces."""
    return f"var(--tt-{status})"


def _esc(s: str) -> str:
    return html.escape(str(s))


def _pretty(s: str) -> str:
    return s.replace("_", " ")


# ---------------------------------------------------------------------------
# shared helpers (used by markdown too)
# ---------------------------------------------------------------------------


def _provenance_tag(item: EvidenceItem) -> str:
    return source_of(item).provenance_tag


def _cite_inline(item: EvidenceItem) -> str:
    src = source_of(item)
    if is_live(item):
        return f"↳ source: {src.name} ({src.citation}; doi:{src.doi}), accession `{item.provenance_group}` — {src.validation}"
    return f"↳ source: `{item.source}` (primary paper) — {src.validation}"


def _effect_str(item: EvidenceItem) -> str:
    e = item.effect
    if e is None:
        return "no effect size on record"
    ci = f" (95% CI {e.ci_low}–{e.ci_high})" if e.is_precise else " (no CI)"
    null = " [crosses null]" if e.is_null else ""
    return f"{e.value} {e.units}{ci}{null}"


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
# spider chart (inline SVG radar, 8 axes, 0..3) -- theme-aware via CSS classes
# ---------------------------------------------------------------------------


def spider_svg(profile: dict[str, int], min_ident: int, size: int = 360) -> str:
    pad = size * 0.16
    cx = cy = size / 2
    radius = (size - 2 * pad) / 2
    n = len(_AXES)

    def point(i: int, value: float, scale: float = 1.0) -> tuple[float, float]:
        angle = -math.pi / 2 + 2 * math.pi * i / n
        r = radius * (value / 3.0) * scale
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    parts = [
        f'<svg viewBox="0 0 {size} {size}" class="radar" role="img" '
        f'aria-label="Causal Strength Profile radar, 8 axes scored 0 to 3">'
    ]
    # grid rings
    for ring in (1, 2, 3):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, ring) for i in range(n)))
        parts.append(f'<polygon points="{pts}" class="ring"/>')
    # gate ring: the identification ceiling. Corroboration beyond it cannot lift the tier.
    if min_ident < 3:
        gpts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, min_ident) for i in range(n)))
        parts.append(f'<polygon points="{gpts}" class="gate"/>')
    # spokes + ring scale numbers (up the top axis)
    for i in range(n):
        x, y = point(i, 3)
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" class="spoke"/>')
    for ring in (1, 2, 3):
        _, ry = point(0, ring)
        parts.append(f'<text x="{cx + 4:.1f}" y="{ry:.1f}" class="ringlab">{ring}</text>')
    # axis labels
    for i, axis in enumerate(_AXES):
        lx, ly = point(i, 3.62)
        fam = "a" if axis.startswith("A") else "b"
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" class="axlab {fam}" text-anchor="middle" '
            f'dominant-baseline="middle">{axis}</text>'
        )
    # data polygon + dots
    dpts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, profile[a]) for i, a in enumerate(_AXES)))
    parts.append(f'<polygon points="{dpts}" class="data"/>')
    for i, a in enumerate(_AXES):
        x, y = point(i, profile[a])
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" class="dot"/>')
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# HTML fragment builders
# ---------------------------------------------------------------------------


def _tier_scale(composite: str) -> str:
    segs = []
    for t in _TIER_ORDER:
        active = "active" if t == composite else ""
        status = _TIER_STATUS[t]
        segs.append(
            f'<div class="seg {active}" style="--c:{_status_var(status)};--ct:{_status_text(status)}">'
            f'<span>{_esc(_TIER_LABEL[t])}</span></div>'
        )
    return f'<div class="scale" aria-label="verdict tier scale, best to worst">{"".join(segs)}</div>'


def _dimension_bars(appraisal: TargetAppraisal) -> str:
    rows = []
    order = ["intervention", "genetic", "temporal", "mediation", "mechanism", "association", "robustness"]
    dims = {d.value: a for d, a in appraisal.dimensions.items()}
    for name in order:
        a = dims.get(name)
        tier = a.tier.value if a else "absent"
        n_items = len(a.items) if a else 0
        rank = _DIM_TIER_RANK[tier]
        width = max(6, int(rank / 3 * 100)) if tier != "absent" else 6
        status = _DIM_TIER_STATUS[tier]
        explain = _DIM_EXPLAIN.get(name, "")
        count = f'<span class="dim-count">{n_items} record{"s" if n_items != 1 else ""}</span>' if n_items else ""
        rows.append(
            f'<div class="dim"><div class="dim-head"><span class="dim-name">{_esc(_pretty(name))}</span>'
            f'<span class="dim-tier" style="color:{_status_text(status)}">{_esc(tier)}</span>{count}</div>'
            f'<div class="dim-track"><div class="dim-fill" style="width:{width}%;background:{_status_var(status)}"></div></div>'
            f'<div class="dim-explain">{_esc(explain)}</div></div>'
        )
    return "".join(rows)


def _tag_html(item: EvidenceItem) -> str:
    tag = _provenance_tag(item).strip("[]")
    cls = "tag-live" if is_live(item) else "tag-unver"
    return f'<span class="tag {cls}">{_esc(tag)}</span>'


def _evidence_card(item: EvidenceItem, dim_tier: str) -> str:
    src = source_of(item)
    direction = _DIRECTION_PLAIN.get(item.direction.value, item.direction.value)
    cite_line = (
        f"{_esc(src.name)} · {_esc(src.citation)}"
        if is_live(item)
        else f"{_esc(item.source)} (primary paper)"
    )
    return (
        f'<div class="ev">'
        f'<div class="ev-top">{_tag_html(item)}<b>{_esc(_pretty(item.evidence_type.value))}</b>'
        f'<span class="muted">{_esc(_pretty(item.dimension.value))} · {_esc(direction)}</span></div>'
        f'<div class="ev-effect">{_esc(_effect_str(item))}</div>'
        f'<div class="ev-meta"><span class="chip">scored: {_esc(dim_tier)}</span>'
        f'<span class="chip">{_esc(_pretty(item.system.value))} / {_esc(_pretty(item.readout.value))}</span></div>'
        f'<div class="ev-cite">{cite_line}</div>'
        + (f'<div class="ev-note">{_esc(item.notes)}</div>' if item.notes else "")
        + "</div>"
    )


def _sources_analysis(appraisal: TargetAppraisal) -> str:
    # group items by data source, remembering the dimension tier each fed
    grouped: dict[str, dict] = {}
    for dim, assessment in appraisal.dimensions.items():
        for it in assessment.items:
            src = source_of(it)
            g = grouped.setdefault(src.id, {"src": src, "rows": []})
            g["rows"].append((it, assessment.tier.value))
    if not grouped:
        return '<p class="muted">No sources returned records for this question.</p>'

    blocks = []
    for g in grouped.values():
        src = g["src"]
        header = (
            f'<div class="src-head"><b>{_esc(src.name)}</b>'
            f'<span class="tag {"tag-live" if src.id in ("opentargets","gnomad") else "tag-unver"}">'
            f'{_esc(src.provenance_tag.strip("[]"))}</span></div>'
            f'<div class="src-sub">{_esc(src.access_class)} · {_esc(src.retrieval)}'
            + (f' · cite: {_esc(src.citation)}' if src.citation else "")
            + f'<br><span class="muted">{_esc(src.validation)}</span></div>'
        )
        trs = []
        for it, tier in g["rows"]:
            direction = _DIRECTION_PLAIN.get(it.direction.value, it.direction.value)
            trs.append(
                f"<tr><td>{_esc(_pretty(it.evidence_type.value))}</td>"
                f"<td>{_esc(_pretty(it.dimension.value))}</td>"
                f"<td>{_esc(direction)}</td>"
                f"<td>{_esc(_effect_str(it))}</td>"
                f'<td><b style="color:{_status_text(_DIM_TIER_STATUS.get(tier,"muted"))}">{_esc(tier)}</b></td></tr>'
            )
        table = (
            '<div class="table-wrap"><table class="src-table"><thead><tr>'
            "<th>what was retrieved</th><th>dimension</th><th>direction</th>"
            "<th>effect</th><th>scorer’s tier</th></tr></thead><tbody>"
            + "".join(trs)
            + "</tbody></table></div>"
        )
        blocks.append(f'<div class="src-card">{header}{table}</div>')
    return "".join(blocks)


def _pipeline(appraisal: TargetAppraisal, q: Optional[Question]) -> str:
    n_sources = len({source_of(it).id for a in appraisal.dimensions.values() for it in a.items})
    n_records = sum(len(a.items) for a in appraisal.dimensions.values())
    steps = [
        ("Question typed", f"{_esc(appraisal.target)} → {_esc(appraisal.disease)}"),
        ("Evidence stack chosen", "modalities that can establish this arrow"),
        ("Databases queried", f"{n_sources} source(s), {n_records} record(s)"),
        ("Tiered by dimension", "each design scored on its own merits"),
        ("Identification gate", "the ceiling = weakest identification axis"),
        ("Verdict", _esc(_TIER_LABEL.get(appraisal.composite.value, appraisal.composite.value))),
    ]
    chips = '<div class="arrow">→</div>'.join(
        f'<div class="pstep"><div class="pstep-t">{t}</div><div class="pstep-d">{d}</div></div>'
        for t, d in steps
    )
    return f'<div class="pipeline">{chips}</div>'


def _four_explanation(appraisal: TargetAppraisal) -> str:
    gen = appraisal.dimensions.get(Dimension.GENETIC)
    temporal = appraisal.dimensions.get(Dimension.TEMPORAL)
    x_to_y = "supported" if appraisal.composite.value in ("causal_driver", "likely_causal") else "open"
    rev = "addressed (genotype fixed at conception)" if gen else "open"
    conf = "addressed by genetic randomization" if gen else "open"
    coll = "modeled" if temporal else "acknowledged, not fully modeled"
    rows = [
        ("X → Y (causal)", "MR + coloc; isogenic knock-in / rescue", x_to_y),
        ("Y → X (reverse causation)", "instrument fixed at conception; longitudinal", rev),
        ("Z → X, Z → Y (confounding)", "randomized / MR; conditional KO", conf),
        ("X → S ← Y (collider / selection)", "population sampling; IPW", coll),
    ]
    trs = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
    return (
        '<div class="table-wrap"><table><thead><tr><th>Rival explanation</th>'
        "<th>Design that rules it out</th><th>Status here</th></tr></thead><tbody>"
        + trs
        + "</tbody></table></div>"
    )


def _references(appraisal: TargetAppraisal) -> str:
    seen: dict[str, EvidenceItem] = {}
    for a in appraisal.dimensions.values():
        for it in a.items:
            seen.setdefault(it.provenance_group, it)
    lis = [
        f'<li>{_tag_html(it)} <code>{_esc(it.source)}</code> — {_esc(cite(it))}</li>'
        for it in seen.values()
    ]
    return "<ul class=\"refs\">" + "".join(lis) + "</ul>" if lis else "<p class='muted'>No records.</p>"


# ---------------------------------------------------------------------------
# Markdown  (unchanged surface; used by the CLI and as an accessible text view)
# ---------------------------------------------------------------------------


def to_markdown(appraisal: TargetAppraisal, q: Optional[Question] = None) -> str:
    profile = csp_profile(appraisal.dimensions)
    min_ident = min(profile[a] for a in ("A1", "A2", "A3", "A4"))
    for_items, against_items = _split_for_against(appraisal)
    L: list[str] = []

    L.append(f"# Causal evidence appraisal — {appraisal.target} → {appraisal.disease}\n")
    L.append("## 1. Verdict (BLUF)\n")
    L.append(f"**Headline tier: `{appraisal.composite.value}`** — {_TIER_MEANING.get(appraisal.composite.value,'')}\n")
    L.append(f"- **Structural position:** `{appraisal.archetype.value}` — {_ARCHETYPE_MEANING.get(appraisal.archetype.value,'')}")
    L.append(f"- **Necessity × sufficiency:** `{appraisal.inus.box.value}` — {appraisal.inus.therapeutic_note}")
    L.append(f"- **Scope:** {appraisal.context.describe()}")
    conf = appraisal.posterior.render() if appraisal.posterior else "confidence not scored"
    L.append(f"- **Subordinate confidence:** {conf} *(never exceeds the tier; digits shown only once calibrated)*")
    L.append(f"\n> {appraisal.archetype_rationale}\n")
    all_items = [it for a in appraisal.dimensions.values() for it in a.items]
    L.append(f"> ⚠️ **Validation required.** {validation_banner(all_items)}\n")

    L.append("## 2. Causal question & estimand\n")
    for slot, val in _estimand(appraisal, q).items():
        L.append(f"- **{slot}:** {val}")
    L.append("")

    L.append("## 3. Evidence FOR\n")
    for it in for_items:
        L.append(f"- {_provenance_tag(it)} **{it.evidence_type.value}** ({it.dimension.value}, {it.direction.value}): {_effect_str(it)}")
        L.append(f"    - {_cite_inline(it)}")
    if not for_items:
        L.append("- None on record.")
    L.append("")

    L.append("## 4. Evidence AGAINST / informative nulls\n")
    for it in against_items:
        L.append(f"- {_provenance_tag(it)} **{it.evidence_type.value}** ({it.dimension.value}, {it.direction.value}): {_effect_str(it)}")
        L.append(f"    - {_cite_inline(it)}")
    if not against_items:
        L.append("- No informative nulls on record.")
    L.append("")

    L.append("## 5. Causal Strength Profile (CSP)\n")
    _binding = [RUBRIC["axes"][a]["name"] for a in ("A1", "A2", "A3", "A4") if profile[a] == min_ident]
    L.append(f"Weakest identification axis (A1..A4 min) = **{min_ident}/3** ({', '.join(_binding)}). "
             f"Identification is the ceiling — corroboration (B-axes) cannot lift a claim past it.\n")
    for a in _AXES:
        fam = "identification" if a.startswith("A") else "corroboration"
        L.append(f"- {a} {RUBRIC['axes'][a]['name']}: {profile[a]}/3 ({fam})")
    L.append("")

    L.append("## 6. Data & databases\n")
    used = {source_of(it).id: source_of(it) for a in appraisal.dimensions.values() for it in a.items}
    for src in used.values():
        L.append(f"- **{src.name}** — {src.access_class}; {src.retrieval}. Cite: {src.citation}")
    if appraisal.not_examined:
        for d in appraisal.not_examined:
            L.append(f"- Gap — {d.value}: not queried. {appraisal.stopped_because or ''}")
    L.append("")

    L.append("## 7. What would change the verdict\n")
    L.append(f"- **Next experiment:** {appraisal.next_experiment}")
    if appraisal.conflicts:
        for c in appraisal.conflicts:
            L.append(f"- Conflict: {c}")
    L.append("")

    L.append("## 8. References\n")
    seen: dict[str, EvidenceItem] = {}
    for a in appraisal.dimensions.values():
        for it in a.items:
            seen.setdefault(it.provenance_group, it)
    for it in seen.values():
        L.append(f"- {_provenance_tag(it)} `{it.source}` — {cite(it)}")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# HTML  (the designed, user-facing report)
# ---------------------------------------------------------------------------

_CSS = """
:root{
 --page:#f9f9f7; --surface:#ffffff; --surface-2:#fcfcfb;
 --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781;
 --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,.10);
 /* vivid: fills, marks, borders, bar fills */
 --blue:#2a78d6; --aqua:#1baf7a; --good:#0ca30c; --warning:#eda100;
 --serious:#ec835a; --critical:#d03b3b; --data-fill:rgba(42,120,214,.16);
 /* text-safe: darker so colored WORDS stay readable on the light surface */
 --tt-good:#0a7d2f; --tt-blue:#1f5fab; --tt-warning:#7a5300;
 --tt-serious:#a8492a; --tt-critical:#b02a2a; --tt-muted:#52514e;
}
@media (prefers-color-scheme:dark){:root{
 --page:#0d0d0d; --surface:#1a1a19; --surface-2:#201f1e;
 --ink:#fff; --ink-2:#c3c2b7; --muted:#898781;
 --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10);
 --blue:#3987e5; --aqua:#199e70; --good:#0ca30c; --warning:#c98500;
 --serious:#ec835a; --critical:#e05a5a; --data-fill:rgba(57,135,229,.22);
 --tt-good:#34d17a; --tt-blue:#6aa8f0; --tt-warning:#e6b24d;
 --tt-serious:#f0a07a; --tt-critical:#ef6b6b; --tt-muted:#c3c2b7;
}}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);
 font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.55;}
.wrap{max-width:940px;margin:0 auto;padding:24px 18px 64px;}
h1{font-size:20px;margin:0 0 2px} h2{font-size:16px;margin:34px 0 12px}
.sub{color:var(--muted);font-size:13px;margin:0 0 18px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px 20px;margin:14px 0;}
.muted{color:var(--muted)} b{font-weight:650}
/* hero */
.hero{display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start;}
.badge{display:inline-flex;flex-direction:column;gap:2px;padding:12px 16px;border-radius:12px;
 border:1px solid var(--border);min-width:180px;background:var(--surface-2);}
.badge .lab{font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted)}
.badge .val{font-size:22px;font-weight:750;line-height:1.15}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;flex:1;min-width:260px}
.tile{background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:10px 12px}
.tile .lab{font-size:10.5px;letter-spacing:.4px;text-transform:uppercase;color:var(--muted)}
.tile .v{font-size:14px;font-weight:600;margin-top:2px}
.rationale{margin-top:14px;padding-left:12px;border-left:3px solid var(--blue);color:var(--ink-2);font-size:14px}
.meaning{margin-top:10px;font-size:13.5px;color:var(--ink-2)}
.validate{background:color-mix(in srgb,var(--warning) 14%,var(--surface));
 border:1px solid color-mix(in srgb,var(--warning) 45%,var(--border));
 border-radius:10px;padding:10px 14px;margin:14px 0;font-size:13px}
/* verdict scale */
.scale{display:flex;gap:4px;margin-top:6px}
.scale .seg{flex:1;text-align:center;font-size:11px;padding:8px 4px;border-radius:8px;
 background:var(--surface-2);border:1px solid var(--border);color:var(--muted)}
.scale .seg.active{color:var(--ct);background:color-mix(in srgb,var(--c) 20%,var(--surface));border-color:var(--c);font-weight:700}
/* dimension bars */
.dim{margin:12px 0}
.dim-head{display:flex;align-items:baseline;gap:10px;font-size:13.5px}
.dim-name{font-weight:650;text-transform:capitalize;min-width:96px}
.dim-tier{font-weight:700;text-transform:capitalize;font-size:12.5px}
.dim-count{color:var(--muted);font-size:12px;margin-left:auto}
.dim-track{height:9px;background:var(--surface-2);border:1px solid var(--border);border-radius:6px;margin:5px 0 3px;overflow:hidden}
.dim-fill{height:100%;border-radius:6px 4px 4px 6px}
.dim-explain{font-size:12px;color:var(--muted)}
/* radar */
.radar-wrap{display:flex;flex-wrap:wrap;gap:20px;align-items:center}
.radar{width:100%;max-width:360px;height:auto}
.radar .ring{fill:none;stroke:var(--grid);stroke-width:1}
.radar .spoke{stroke:var(--grid);stroke-width:1}
.radar .gate{fill:none;stroke:var(--critical);stroke-width:1.6;stroke-dasharray:4 3;opacity:.75}
.radar .axlab{font:650 12px system-ui}
.radar .axlab.a{fill:var(--blue)} .radar .axlab.b{fill:var(--aqua)}
.radar .ringlab{font:11px system-ui;fill:var(--muted)}
.radar .data{fill:var(--data-fill);stroke:var(--blue);stroke-width:2}
.radar .dot{fill:var(--blue)}
.radar-key{flex:1;min-width:230px;font-size:13px}
.radar-key .fam{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.axis-list{margin:8px 0 0;padding:0;list-style:none;font-size:12.5px}
.axis-list li{display:flex;justify-content:space-between;gap:12px;padding:3px 0;border-bottom:1px dashed var(--border)}
.axis-list .sc{font-variant-numeric:tabular-nums;color:var(--ink-2)}
/* pipeline */
.pipeline{display:flex;flex-wrap:wrap;align-items:stretch;gap:6px}
.pstep{background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:8px 11px;flex:1;min-width:120px}
.pstep-t{font-size:12.5px;font-weight:650} .pstep-d{font-size:11px;color:var(--muted);margin-top:2px}
.arrow{align-self:center;color:var(--muted);font-size:15px}
/* sources */
.src-card{border:1px solid var(--border);border-radius:12px;padding:12px 14px;margin:12px 0;background:var(--surface-2)}
.src-head{display:flex;align-items:center;gap:8px;font-size:14px}
.src-sub{font-size:12px;color:var(--ink-2);margin:4px 0 8px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.3px}
.table-wrap{overflow-x:auto}
/* evidence cards */
.ev-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.ev{background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:10px 12px;font-size:13px}
.ev-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.ev-effect{font-weight:600;margin:6px 0}
.ev-meta{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px}
.chip{font-size:11px;background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:2px 8px;color:var(--ink-2)}
.ev-cite{font-size:11.5px;color:var(--muted)}
.ev-note{font-size:11.5px;color:var(--ink-2);margin-top:6px;font-style:italic}
.tag{font-size:10px;font-weight:700;letter-spacing:.4px;padding:2px 7px;border-radius:5px}
.tag-live{background:color-mix(in srgb,var(--blue) 18%,var(--surface));color:var(--blue)}
.tag-unver{background:color-mix(in srgb,var(--warning) 20%,var(--surface));color:var(--warning)}
.refs{font-size:12.5px;padding-left:18px} .refs li{margin:5px 0} code{font-size:12px}
.explainer{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;font-size:13px}
.explainer div b{color:var(--ink)}
.next{background:color-mix(in srgb,var(--good) 10%,var(--surface));border:1px solid color-mix(in srgb,var(--good) 35%,var(--border));border-radius:10px;padding:12px 14px;font-size:13.5px}
.warn-list{font-size:13px;color:var(--ink-2)}
"""


def to_html(appraisal: TargetAppraisal, q: Optional[Question] = None) -> str:
    profile = csp_profile(appraisal.dimensions)
    ident_axes = ("A1", "A2", "A3", "A4")
    min_ident = min(profile[a] for a in ident_axes)
    binding = [RUBRIC["axes"][a]["name"] for a in ident_axes if profile[a] == min_ident]
    binding_clause = f", here <b>{_esc(', '.join(binding))}</b>" if binding else ""
    svg = spider_svg(profile, min_ident)
    for_items, against_items = _split_for_against(appraisal)
    tier = appraisal.composite.value
    tier_border = _status_var(_TIER_STATUS.get(tier, "muted"))   # vivid: badge border
    tier_text = _status_text(_TIER_STATUS.get(tier, "muted"))    # text-safe: the big word
    all_items = [it for a in appraisal.dimensions.values() for it in a.items]

    # axis list (accessible table view of the radar)
    axis_rows = "".join(
        f'<li><span>{a} · {_esc(RUBRIC["axes"][a]["name"])} '
        f'<span class="muted">({"identification" if a.startswith("A") else "corroboration"})</span></span>'
        f'<span class="sc">{profile[a]}/3</span></li>'
        for a in _AXES
    )

    estimand_rows = "".join(
        f"<tr><td><b>{_esc(k)}</b></td><td>{_esc(v)}</td></tr>" for k, v in _estimand(appraisal, q).items()
    )

    conf = appraisal.posterior.render() if appraisal.posterior else "not scored"

    for_html = (
        '<div class="ev-grid">'
        + "".join(_evidence_card(it, appraisal.dimensions[it.dimension].tier.value) for it in for_items)
        + "</div>"
        if for_items
        else '<p class="muted">No directional evidence in favour on record.</p>'
    )
    against_html = (
        '<div class="ev-grid">'
        + "".join(_evidence_card(it, appraisal.dimensions[it.dimension].tier.value) for it in against_items)
        + "</div>"
        if against_items
        else '<p class="muted">No informative null / contradicting evidence on record.</p>'
    )

    conflicts_html = (
        "".join(f"<li>{_esc(c)}</li>" for c in appraisal.conflicts)
        if appraisal.conflicts
        else "<li class='muted'>No directional conflicts among the evidence.</li>"
    )
    gaps_html = (
        "".join(
            f"<li><b>{_esc(_pretty(d.value))}</b> not queried this run. {_esc(appraisal.stopped_because or '')}</li>"
            for d in appraisal.not_examined
        )
        if appraisal.not_examined
        else "<li class='muted'>No unexamined causal dimensions for this arrow.</li>"
    )
    limits_html = "".join(f"<li>{_esc(l)}</li>" for l in appraisal.known_limitations)
    coarse = (
        '<p class="validate">⚠️ The disease term maps to many subtypes; a stratified verdict is advised.</p>'
        if appraisal.coarse_label_warning
        else ""
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CAUala — {_esc(appraisal.target)} → {_esc(appraisal.disease)}</title>
<style>{_CSS}</style></head>
<body><div class="wrap">

<h1>{_esc(appraisal.target)} → {_esc(appraisal.disease)}</h1>
<p class="sub">Causal evidence appraisal · scope: {_esc(appraisal.context.describe())}</p>

<div class="card">
  <div class="hero">
    <div class="badge" style="border-color:{tier_border}">
      <span class="lab">Verdict tier</span>
      <span class="val" style="color:{tier_text}">{_esc(_TIER_LABEL.get(tier, tier))}</span>
    </div>
    <div class="tiles">
      <div class="tile"><div class="lab">Structural position</div><div class="v">{_esc(_pretty(appraisal.archetype.value))}</div></div>
      <div class="tile"><div class="lab">Necessity × sufficiency</div><div class="v">{_esc(_pretty(appraisal.inus.box.value))}</div></div>
      <div class="tile"><div class="lab">Confidence</div><div class="v">{_esc(conf)}</div></div>
    </div>
  </div>
  <div class="meaning"><b>What this means:</b> {_esc(_TIER_MEANING.get(tier,''))}</div>
  <div class="rationale">{_esc(appraisal.archetype_rationale)}</div>
</div>

<p class="validate">⚠️ <b>Validation required.</b> {_esc(validation_banner(all_items))}</p>

<h2>Where this verdict sits</h2>
<div class="card">
  {_tier_scale(tier)}
  <p class="meaning" style="margin-top:12px"><b>Position ({_esc(_pretty(appraisal.archetype.value))}):</b> {_esc(_ARCHETYPE_MEANING.get(appraisal.archetype.value,''))}</p>
  <p class="meaning"><b>Necessity × sufficiency:</b> {_esc(appraisal.inus.therapeutic_note)}</p>
</div>

<h2>How to read this report</h2>
<div class="card explainer">
  <div><b>Tier</b> is the headline — the honest ceiling set by the strongest causal evidence present. Association and mechanism alone cap at “Unvalidated.”</div>
  <div><b>Position</b> says where the target sits in the causal graph — a driver, a marker, an upstream initiator, and so on. A score can’t say this; the label can.</div>
  <div><b>Necessity × sufficiency</b> asks two different questions: is the target required, and is it enough? They need different experiments.</div>
  <div><b>Confidence</b> is deliberately subordinate to the tier and shown as a band, not a bare number, until the tool is calibrated on a gold-standard set.</div>
  <div><b>The core idea:</b> correlation with a disease and causal position are different axes. A marker can correlate beautifully and still not be a cause. CAUala <b>gates</b> — it never lets a mechanism story sum its way to a high score.</div>
</div>

<h2>Evidence strength by dimension</h2>
<div class="card">
  <p class="sub" style="margin:0 0 6px">Each dimension is a different causal question, scored on its own merits. Only the causal dimensions can raise the tier.</p>
  {_dimension_bars(appraisal)}
</div>

<h2>Causal Strength Profile</h2>
<div class="card">
  <div class="radar-wrap">
    {svg}
    <div class="radar-key">
      <div><span class="fam" style="background:var(--blue)"></span><b>A1–A4 · Identification</b> — did we rule out the rival explanations? These set the ceiling.</div>
      <div style="margin-top:4px"><span class="fam" style="background:var(--aqua)"></span><b>B1–B4 · Corroboration</b> — how strong is the positive signal?</div>
      <ul class="axis-list">{axis_rows}</ul>
    </div>
  </div>
  <p class="meaning" style="margin-top:12px"><b>The identification gate.</b> The dashed ring sits at the weakest identification axis (A1–A4 min = {min_ident} of 3){binding_clause}. Identification is the ceiling on any causal claim: however large the corroboration shape grows on the B side, it cannot make up for a gap on the A side. That is why the <i>shape</i> of this profile matters more than its area — two targets with the same area can be identified very differently.</p>
</div>

<h2>Data sources &amp; how they were analyzed</h2>
<div class="card">
  <p class="sub" style="margin:0 0 8px">Exactly what each database returned, and the tier the deterministic scorer assigned to it. Direction-less scores (an integrated association, a constraint metric) can add strength but never set a causal tier by themselves.</p>
  {_sources_analysis(appraisal)}
</div>

<h2>How the analysis works</h2>
<div class="card">
  {_pipeline(appraisal, q)}
  <h3 style="font-size:13.5px;margin:18px 0 6px">The estimand — the exact question, as an intervention</h3>
  <div class="table-wrap"><table><tbody>{estimand_rows}</tbody></table></div>
  <h3 style="font-size:13.5px;margin:18px 0 6px">Ruling out the four rival explanations</h3>
  {_four_explanation(appraisal)}
</div>

<h2>Evidence in favour</h2>
<div class="card">{for_html}</div>

<h2>Evidence against &amp; informative nulls</h2>
<div class="card">{against_html}</div>

<h2>What would change the verdict</h2>
<div class="card">
  <div class="next"><b>Next experiment</b> (the weakest dimension, most cheaply strengthened): {_esc(appraisal.next_experiment)}</div>
  <h3 style="font-size:13.5px;margin:16px 0 6px">Conflicts (surfaced, never averaged away)</h3>
  <ul class="warn-list">{conflicts_html}</ul>
  <h3 style="font-size:13.5px;margin:16px 0 6px">Named gaps (not queried this run)</h3>
  <ul class="warn-list">{gaps_html}</ul>
</div>

<h2>Honest limitations</h2>
<div class="card">
  {coarse}
  <ul class="warn-list">{limits_html}</ul>
</div>

<h2>References &amp; provenance</h2>
<div class="card">{_references(appraisal)}</div>

</div></body></html>"""


def to_json(appraisal: TargetAppraisal) -> str:
    payload = json.loads(appraisal.model_dump_json())
    payload["csp_profile"] = csp_profile(appraisal.dimensions)
    payload["verdict_line"] = appraisal.verdict_line()
    all_items = [it for a in appraisal.dimensions.values() for it in a.items]
    payload["provenance"] = {
        "validation_banner": validation_banner(all_items),
        "sources": [
            {
                "source": it.source,
                "provenance_group": it.provenance_group,
                "datasource": source_of(it).name,
                "provenance_tag": source_of(it).provenance_tag,
                "live": is_live(it),
                "citation": cite(it),
            }
            for it in {it.provenance_group: it for a in appraisal.dimensions.values() for it in a.items}.values()
        ],
    }
    return json.dumps(payload, indent=2)
