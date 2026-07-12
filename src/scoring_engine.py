"""
Scoring-engine layer: everything the deterministic core needs beyond the gate.

`scoring.py` answers "which tier / which archetype" from a dimension vector.
This module supplies the rest of the appraisal, all deterministic:

  * assemble_dimension  -- turn retrieved EvidenceItems into a DimensionAssessment
                           (tiering, directionality gate, confounder downgrade).
  * csp_profile         -- the 8-axis Causal Strength Profile (best-per-axis).
  * gated_tier_from_csp -- the identification gate: overall tier <= min(A1..A4).
  * derive_inus         -- necessity / sufficiency arms from LOF / GOF evidence.
  * compute_posterior   -- the SUBORDINATE posterior, clamped under the gate.
  * voi_should_stop     -- value-of-information stopping.

Nothing here is calibrated: the posterior ships `calibrated=False` and renders as
a band until the validation harness runs. The LLM never enters this file.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

import yaml

from src.schema import (
    Assumption,
    Composite,
    Dimension,
    DimensionAssessment,
    Direction,
    EvidenceItem,
    EvidenceType,
    InusVerdict,
    NSAxis,
    Posterior,
    Tier,
)

_RUBRIC_PATH = Path(__file__).resolve().parent.parent / "scoring" / "rubric.yaml"


def load_rubric() -> dict:
    with open(_RUBRIC_PATH) as fh:
        return yaml.safe_load(fh)


RUBRIC = load_rubric()

# Evidence types that carry NO direction. Invariant #1: these move
# strength/consistency only -- never temporality, direction, or the
# driver-vs-mediator call, and never the posterior.
DIRECTIONLESS_TYPES: frozenset[EvidenceType] = frozenset(
    {
        EvidenceType.CROSS_SECTIONAL,
        EvidenceType.EXPRESSION_CONCORDANCE,
        EvidenceType.BIOCHEMICAL_PATHWAY,
        EvidenceType.OBSERVATIONAL_COHORT,
    }
)

# Base tier each study design can reach (before confounder/context downgrade).
_TYPE_BASE_TIER: dict[EvidenceType, Tier] = {
    EvidenceType.HUMAN_RCT: Tier.STRONG,
    EvidenceType.HUMAN_CELL_PERTURBATION: Tier.MODERATE,
    EvidenceType.ANIMAL_PERTURBATION: Tier.WEAK,
    EvidenceType.RARE_PENETRANT_VARIANT: Tier.STRONG,
    EvidenceType.PROTECTIVE_ALLELE: Tier.STRONG,
    EvidenceType.ALLELIC_SERIES: Tier.STRONG,
    EvidenceType.MENDELIAN_RANDOMIZATION: Tier.MODERATE,
    EvidenceType.GWAS_COLOCALIZATION: Tier.MODERATE,
    EvidenceType.GWAS_NEAREST_GENE: Tier.WEAK,
    EvidenceType.LONGITUDINAL_COHORT: Tier.MODERATE,
    EvidenceType.ANCHORED_ONSET_COHORT: Tier.STRONG,
    EvidenceType.FORMAL_MEDIATION: Tier.MODERATE,
    EvidenceType.PATHWAY_EPISTASIS: Tier.MODERATE,
    EvidenceType.BIOCHEMICAL_PATHWAY: Tier.STRONG,      # mechanism dim only
    EvidenceType.EXPRESSION_CONCORDANCE: Tier.WEAK,
    EvidenceType.CROSS_SECTIONAL: Tier.WEAK,
    EvidenceType.OBSERVATIONAL_COHORT: Tier.MODERATE,
    EvidenceType.REPLICATION: Tier.MODERATE,
    EvidenceType.SENSITIVITY_ANALYSIS: Tier.WEAK,
}

# Numeric weight of each design for the (subordinate) posterior log-odds update.
# Direction-less types are 0 by construction -- they cannot move the posterior.
_TYPE_POSTERIOR_WEIGHT: dict[EvidenceType, float] = {
    EvidenceType.HUMAN_RCT: 3.0,
    EvidenceType.HUMAN_CELL_PERTURBATION: 1.6,
    EvidenceType.ANIMAL_PERTURBATION: 0.9,
    EvidenceType.RARE_PENETRANT_VARIANT: 2.2,
    EvidenceType.PROTECTIVE_ALLELE: 2.4,
    EvidenceType.ALLELIC_SERIES: 2.4,
    EvidenceType.MENDELIAN_RANDOMIZATION: 2.2,
    EvidenceType.GWAS_COLOCALIZATION: 1.4,
    EvidenceType.GWAS_NEAREST_GENE: 0.6,
    EvidenceType.LONGITUDINAL_COHORT: 0.9,
    EvidenceType.ANCHORED_ONSET_COHORT: 1.3,
    EvidenceType.FORMAL_MEDIATION: 0.9,
    EvidenceType.PATHWAY_EPISTASIS: 1.0,
    EvidenceType.REPLICATION: 0.5,
    EvidenceType.SENSITIVITY_ANALYSIS: 0.3,
}

_TIER_ORDER = {Tier.STRONG: 3, Tier.MODERATE: 2, Tier.WEAK: 1, Tier.ABSENT: 0}

# Posterior ceiling per composite tier (mirrors TargetAppraisal.posterior_respects_gate).
_CEILING: dict[Composite, float] = {
    Composite.CAUSAL_DRIVER: 0.99,
    Composite.LIKELY_CAUSAL: 0.90,
    Composite.PLAUSIBLE: 0.66,
    Composite.UNVALIDATED: 0.50,
    Composite.LIKELY_NONCAUSAL: 0.33,
    Composite.REFUTED: 0.10,
}


# ---------------------------------------------------------------------------
# Retrieval -> DimensionAssessment
# ---------------------------------------------------------------------------


def _dedupe(items: list[EvidenceItem]) -> list[EvidenceItem]:
    """Ten papers citing one observation are ONE piece of evidence."""
    seen: dict[str, EvidenceItem] = {}
    for it in items:
        seen.setdefault(it.provenance_group, it)
    return list(seen.values())


def _context_match(item: EvidenceItem, context_match_map: Optional[dict[str, float]]) -> float:
    if not context_match_map:
        return 1.0
    return context_match_map.get(item.id, 1.0)


def _is_large_effect(item: EvidenceItem) -> bool:
    """A precise, non-null, appreciably-sized effect. Ratio units judged on the
    log scale (OR/HR <=0.67 or >=1.5); linear units on |value| >= 0.5."""
    eff = item.effect
    if eff is None or not eff.is_precise or eff.is_null:
        return False
    if any(u in eff.units.lower() for u in ("or", "hr", "rr", "ratio")) and eff.value > 0:
        return abs(math.log(eff.value)) >= 0.4
    return abs(eff.value) >= 0.5


def assemble_dimension(
    dimension: Dimension,
    items: list[EvidenceItem],
    context_match_map: Optional[dict[str, float]] = None,
) -> DimensionAssessment:
    """Tier a set of retrieved items for one dimension.

    Rules encoded (gated, not summed):
      * de-duplicate by provenance_group first;
      * a well-powered NULL in a causal design => CONTRADICTED (not "weak");
      * base tier = strongest design present among direction-carrying items;
      * a STRONG-base design reaches STRONG only if CORROBORATED -- replicated
        across >=2 provenance groups OR carrying a large precise effect; a single
        modest instance drops one step (a lone modest RCT is not the same as a
        replicated trial programme);
      * a poor context match drops one further step;
      * direction-less designs cannot lift a causal dimension above WEAK.
    """
    items = _dedupe(items)
    if not items:
        return DimensionAssessment(dimension=dimension, tier=Tier.ABSENT, items=[])

    directional = [i for i in items if i.direction != Direction.NULL]
    nulls = [i for i in items if i.direction == Direction.NULL]

    causal_dim = dimension in (
        Dimension.INTERVENTION,
        Dimension.GENETIC,
        Dimension.TEMPORAL,
        Dimension.MEDIATION,
    )

    # A performed causal design that came back null contradicts the arrow.
    strong_null = any(
        _TYPE_BASE_TIER.get(i.evidence_type, Tier.WEAK) in (Tier.STRONG, Tier.MODERATE)
        for i in nulls
    )
    if causal_dim and strong_null and not directional:
        return DimensionAssessment(
            dimension=dimension,
            tier=Tier.CONTRADICTED,
            items=items,
            contradicting_items=nulls,
            falsifiability="A causal-design null here would reverse only with better instruments.",
        )

    ranked = directional or items
    best = max(
        (_TYPE_BASE_TIER.get(i.evidence_type, Tier.WEAK) for i in ranked),
        key=lambda t: _TIER_ORDER[t],
    )

    # Directionless-only evidence cannot raise a causal dimension above WEAK.
    if causal_dim and all(i.evidence_type in DIRECTIONLESS_TYPES for i in ranked):
        best = Tier.WEAK

    downgrade = 0
    # Corroboration check on the strongest tier: replication OR a large effect.
    if best == Tier.STRONG:
        strong_items = [i for i in ranked if _TYPE_BASE_TIER.get(i.evidence_type) == Tier.STRONG]
        groups = {i.provenance_group for i in strong_items}
        replicated = len(groups) >= 2
        large = any(_is_large_effect(i) for i in strong_items)
        if not (replicated or large):
            downgrade += 1

    # Context penalty: a wrong-context best item is weaker for the asked context.
    if any(_context_match(i, context_match_map) < 0.5 for i in ranked):
        downgrade += 1

    tier_rank = max(0, _TIER_ORDER[best] - downgrade)
    tier = {3: Tier.STRONG, 2: Tier.MODERATE, 1: Tier.WEAK, 0: Tier.WEAK}[tier_rank]

    load_bearing = sorted({a for i in ranked for a in i.assumptions_required}, key=lambda a: a.value)
    return DimensionAssessment(
        dimension=dimension,
        tier=tier,
        items=items,
        assumptions_load_bearing=load_bearing,
        contradicting_items=nulls,
        falsifiability=items[0].falsified_by[0] if items[0].falsified_by else "",
    )


# ---------------------------------------------------------------------------
# CSP profile + identification gate
# ---------------------------------------------------------------------------

_AXES = ("A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4")


def csp_profile(dimensions: dict[Dimension, DimensionAssessment]) -> dict[str, int]:
    """Per-claim CSP: for each axis, the best score any supporting item reaches.

    Uses the per-EvidenceType axis priors from the rubric. This is the *shape* the
    spider chart plots; the identification gate then reads min(A1..A4) off it.
    """
    priors = RUBRIC["evidence_type_axis_priors"]
    profile = {ax: 0 for ax in _AXES}
    for assessment in dimensions.values():
        for item in assessment.items:
            per_type = priors.get(item.evidence_type.value, {})
            for ax, score in per_type.items():
                if ax in profile:
                    profile[ax] = max(profile[ax], int(score))
    return profile


def gated_tier_from_csp(profile: dict[str, int]) -> tuple[int, str]:
    """The identification gate: overall gated tier = min(A1..A4) mapped to a tier.

    Returns (min_identification_score, tier_label). Precision (B-axes) can never
    lift this ceiling -- that is the whole point of the gate.
    """
    min_ident = min(profile[a] for a in ("A1", "A2", "A3", "A4"))
    gate = RUBRIC["identification_gate"][min_ident]
    return min_ident, gate["tier"]


# ---------------------------------------------------------------------------
# INUS arms
# ---------------------------------------------------------------------------

# Loss-of-function designs probe NECESSITY; gain-of-function-in-naive-background
# probes SUFFICIENCY. Direction disambiguates which arm an item speaks to.
_LOF_TYPES = frozenset(
    {EvidenceType.PROTECTIVE_ALLELE, EvidenceType.HUMAN_CELL_PERTURBATION, EvidenceType.ANIMAL_PERTURBATION}
)
_GOF_TYPES = frozenset(
    {EvidenceType.RARE_PENETRANT_VARIANT, EvidenceType.ALLELIC_SERIES, EvidenceType.HUMAN_CELL_PERTURBATION}
)


def derive_inus(dimensions: dict[Dimension, DimensionAssessment]) -> InusVerdict:
    """Necessity and sufficiency scored on SEPARATE arms, then combined into a box.

    necessity  <- loss-of-function evidence (phenotype fails without X?)
    sufficiency<- gain-of-function-in-naive-background evidence (X alone produces it?)

    Kept deliberately conservative: an arm is SUPPORTED only on a directional,
    non-null item; a directional null on the probing design REFUTES it; otherwise
    it stays UNTESTED. The two middle boxes must never collapse together.
    """
    necessity = NSAxis.UNTESTED
    sufficiency = NSAxis.UNTESTED

    for assessment in dimensions.values():
        for item in assessment.items:
            et = item.evidence_type
            is_null = item.direction == Direction.NULL
            # necessity: LOF that reduces disease (DOWN_PROTECTS) supports it.
            if et in _LOF_TYPES and item.direction in (Direction.DOWN_PROTECTS, Direction.UP_HARMS):
                necessity = NSAxis.SUPPORTED
            elif et in _LOF_TYPES and is_null and necessity == NSAxis.UNTESTED:
                necessity = NSAxis.REFUTED
            # sufficiency: GOF in naive background that produces disease (UP_HARMS) supports it.
            if et in _GOF_TYPES and item.direction == Direction.UP_HARMS:
                sufficiency = NSAxis.SUPPORTED
            elif et in _GOF_TYPES and is_null and sufficiency == NSAxis.UNTESTED:
                sufficiency = NSAxis.REFUTED

    return InusVerdict(necessity=necessity, sufficiency=sufficiency)


# ---------------------------------------------------------------------------
# Subordinate posterior
# ---------------------------------------------------------------------------


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def _effect_z(item: EvidenceItem) -> float:
    """A crude within-item magnitude factor in [0.5, 2.0]. Real normalization is
    within-modality; this keeps a precise, large effect from counting the same as
    a null-crossing one without pretending to a calibrated z."""
    eff = item.effect
    if eff is None:
        return 1.0
    if eff.is_null:
        return 0.5
    if not eff.is_precise:
        return 1.0
    # Distance of the point estimate from the null, on a log scale for ratios.
    ratio_units = any(u in eff.units.lower() for u in ("or", "hr", "rr", "ratio"))
    null = 1.0 if ratio_units else 0.0
    magnitude = abs(math.log(eff.value / null)) if ratio_units and eff.value > 0 else abs(eff.value - null)
    return max(0.5, min(2.0, 0.8 + magnitude))


def compute_posterior(
    dimensions: dict[Dimension, DimensionAssessment],
    composite: Composite,
    prior: float,
    prior_source: str,
) -> Posterior:
    """The subordinate posterior: a base-rate prior updated by directional causal
    evidence, then HARD-CLAMPED under the gated tier. Always uncalibrated here.

    value = sigmoid( logit(prior)
                     + Σ_i  w(type)·dir_sign_i·context_i·z_i
                     − Σ_j  penalty_j (untested load-bearing assumptions) )
    then value = min(value, ceiling(composite)).
    """
    log_odds = _logit(prior)
    penalty = 0.0

    causal_dims = (Dimension.INTERVENTION, Dimension.GENETIC, Dimension.TEMPORAL, Dimension.MEDIATION)
    for d in causal_dims:
        assessment = dimensions.get(d)
        if not assessment:
            continue
        for item in _dedupe(assessment.items):
            if item.evidence_type in DIRECTIONLESS_TYPES:
                continue  # gate: no directional credit
            weight = _TYPE_POSTERIOR_WEIGHT.get(item.evidence_type, 0.0)
            if weight == 0.0:
                continue
            z = _effect_z(item)
            if item.direction == Direction.NULL:
                dir_sign = -1.0        # a causal-design null is evidence AGAINST
            else:
                dir_sign = 1.0
            log_odds += 0.35 * weight * dir_sign * z
            # confounder penalty: untested load-bearing assumptions push mass away.
            penalty += 0.15 * len(item.assumptions_required)

    value = _sigmoid(log_odds - penalty)
    ceiling = _CEILING[composite]
    value = min(value, ceiling)

    return Posterior(
        value=value,
        prior=prior,
        prior_source=prior_source,
        calibrated=False,  # digits stay hidden until the validation harness runs
    )


# ---------------------------------------------------------------------------
# Value-of-information stopping
# ---------------------------------------------------------------------------


def voi_should_stop(
    composite: Composite,
    examined_modalities: list[str],
    remaining_stack: list[dict],
    epsilon: float = 0.15,
) -> tuple[bool, str]:
    """Decide whether the best remaining modality could still flip the verdict.

    Stops (with a stated reason, never silently) when:
      * a tier-1 conclusive result is already in hand, or
      * the composite is already REFUTED / CAUSAL_DRIVER (extremes rarely move), or
      * the strongest remaining retrieval-prior tier is too weak to plausibly move
        the verdict given the current state (marginal VOI < epsilon), or
      * the stack is exhausted.
    """
    if not remaining_stack:
        return True, "Evidence stack for this arrow is exhausted; checklist complete."

    if composite in (Composite.CAUSAL_DRIVER, Composite.REFUTED):
        return True, (
            f"Verdict is at an extreme ({composite.value}); no remaining modality's "
            "maximum plausible weight could flip it."
        )

    best_remaining_tier = min(m.get("tier", 5) for m in remaining_stack)  # 1 strongest
    # A remaining modality can only lift the verdict if it can carry more causal
    # weight than what's already resolved. Approximate "could it flip?" by whether
    # a tier<=2 modality is still unqueried.
    marginal = max(0.0, (3 - best_remaining_tier) / 3.0)  # tier1->0.67, tier3->0
    if marginal < epsilon:
        names = ", ".join(m["modality"] for m in remaining_stack)
        return True, (
            f"Marginal value of information below threshold: strongest unqueried "
            f"modality is retrieval-tier {best_remaining_tier} ({names}); it cannot "
            f"move a {composite.value} verdict."
        )

    return False, ""
