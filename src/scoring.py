"""
Deterministic scoring core: the gated ordinal tier and the structural archetype.

Two entry points, both pure functions of the dimension vector:

    apply_gates(dimensions)        -> Composite    (the HEADLINE ordinal tier)
    classify_archetype(dimensions) -> (Archetype, rationale)

The discipline this file enforces, and the reason it is deterministic and
testable rather than an LLM call:

  * We GATE, we never sum. A beautiful mechanism cannot lift the tier (the CETP
    rule): association + mechanism alone cap at UNVALIDATED no matter how strong.
  * CONTRADICTED evidence forces the composite DOWN; it is never averaged away.
  * The top tier (CAUSAL_DRIVER) is unlocked only by BIDIRECTIONAL causal
    evidence plus a successful strong human intervention.
  * Archetype is STRUCTURAL and disease-agnostic. `disease_area` only selects an
    illustration; it can never change the archetype (invariance test).
  * The rationale is a structural sentence that stands alone, optionally followed
    by a "For illustration, ..." clause -- never leaking exemplar tokens into the
    disease-agnostic logic.
"""

from __future__ import annotations

from typing import Optional

from src.exemplars import exemplar_for
from src.schema import (
    Archetype,
    Composite,
    Dimension,
    DimensionAssessment,
    Tier,
)

Dimensions = dict[Dimension, DimensionAssessment]

# Tiers that count as positive causal support.
_SUPPORTIVE = (Tier.STRONG, Tier.MODERATE)
# Tiers that count as weak/absent concurrent correlation (initiator signature).
_WEAKISH = (Tier.WEAK, Tier.ABSENT)

# The four dimensions that can carry causal weight. Association and mechanism are
# deliberately excluded -- they cannot raise the ceiling (invariant #2).
_CAUSAL_DIMS = (
    Dimension.INTERVENTION,
    Dimension.GENETIC,
    Dimension.TEMPORAL,
    Dimension.MEDIATION,
)


def _tier(dimensions: Dimensions, d: Dimension) -> Tier:
    """Tier of a dimension, ABSENT if the dimension was not assessed at all."""
    assessment = dimensions.get(d)
    return assessment.tier if assessment is not None else Tier.ABSENT


def _genetic_is_bidirectional(dimensions: Dimensions) -> bool:
    """increase->harm AND decrease->protect within the genetic dimension."""
    genetic = dimensions.get(Dimension.GENETIC)
    return bool(genetic and genetic.has_bidirectional_support)


# ---------------------------------------------------------------------------
# The gate -> Composite (the headline)
# ---------------------------------------------------------------------------


def apply_gates(dimensions: Dimensions) -> Composite:
    """Return the gated ordinal tier -- the headline verdict.

    Order matters: contradiction is checked before support, and the ceiling is
    set by the strongest *causal* tier present, not by the loudest dimension.
    """
    interv = _tier(dimensions, Dimension.INTERVENTION)
    gen = _tier(dimensions, Dimension.GENETIC)
    temp = _tier(dimensions, Dimension.TEMPORAL)
    med = _tier(dimensions, Dimension.MEDIATION)

    causal_support = [t for t in (interv, gen, temp, med) if t in _SUPPORTIVE]

    # 1. A performed human intervention that FAILED is close to dispositive.
    #    Randomization did the work and the answer came back null.
    if interv == Tier.CONTRADICTED:
        return Composite.REFUTED

    # 2. Nature's randomization (genetics) points the other way and nothing
    #    positive is on the causal axes to weigh against it.
    if gen == Tier.CONTRADICTED and not causal_support:
        return Composite.LIKELY_NONCAUSAL

    # 3. No causal-tier evidence at all. Association + mechanism, however strong,
    #    cap here. This is the CETP rule made mechanical.
    if not causal_support:
        return Composite.UNVALIDATED

    # 4. Some causal support exists but genetics actively contradicts. A genuine
    #    directional conflict: cap at PLAUSIBLE and surface it, never average.
    if gen == Tier.CONTRADICTED:
        return Composite.PLAUSIBLE

    gen_bidirectional = _genetic_is_bidirectional(dimensions)

    # 5. Top tier: bidirectional causal control unlocked, and a strong successful
    #    human intervention converges with it.
    if gen_bidirectional and interv == Tier.STRONG:
        return Composite.CAUSAL_DRIVER

    # 6. Strong causal identification on at least one axis, but not the full
    #    bidirectional-plus-intervention convergence.
    if gen_bidirectional or interv in _SUPPORTIVE or gen == Tier.STRONG or temp == Tier.STRONG:
        return Composite.LIKELY_CAUSAL

    # 7. Some causal support, but only moderate / indirect.
    return Composite.PLAUSIBLE


# ---------------------------------------------------------------------------
# The structural position -> Archetype (+ standalone rationale)
# ---------------------------------------------------------------------------

# Disease-agnostic structural rationales. Each is a complete sentence that ends
# with a period and contains no exemplar token, so the "For illustration" clause
# can be stripped and the sentence still stands (the separation invariant).
_STRUCTURAL_RATIONALE: dict[Archetype, str] = {
    Archetype.VALIDATED_DRIVER: (
        "Converging bidirectional causal evidence -- loss- and gain-of-function "
        "pointing opposite ways -- together with a successful human intervention "
        "place the target on the causal path with the strongest support the "
        "framework assigns."
    ),
    Archetype.ASSOCIATED_NONCAUSAL: (
        "Strong, replicated association coexists with null or contradicted "
        "genetic and interventional evidence, the signature of a marker, not "
        "target: it tracks the outcome without sitting on any causal path to it."
    ),
    Archetype.DISPLACED_SIGNAL: (
        "The measured node correlates while its own genetic evidence is null, and "
        "a neighbouring node in the same pathway carries the causal signal, so the "
        "real association is displaced from the true upstream driver."
    ),
    Archetype.UPSTREAM_INITIATOR: (
        "Strong genetic causal support pairs with weak concurrent correlation, "
        "the signature of a node that acts early in the cascade and whose "
        "association to the measured outcome decays as causal distance grows."
    ),
    Archetype.DOWNSTREAM_MEDIATOR: (
        "Strong association and a plausible mediating position combine with weak "
        "independent genetic support: an excellent biomarker but an uncertain "
        "target, because a mediator IS causal yet its position in the graph is a "
        "relation, not proof of primacy."
    ),
    Archetype.REACTIVE_CONSEQUENCE: (
        "The measured node changes only after disease onset, so on the observed "
        "time axis it cannot be driving what precedes it and reads as a "
        "consequence rather than a cause."
    ),
    Archetype.UNTESTED: (
        "Only mechanistic or associational plausibility is on record, with no "
        "interventional, genetic, temporal, or mediation evidence queried yet, so "
        "this is evidence of nothing, not evidence against."
    ),
}


def _build_rationale(archetype: Archetype, disease_area: Optional[str]) -> str:
    """Structural sentence + optional 'For illustration, ...' clause."""
    structural = _STRUCTURAL_RATIONALE[archetype]
    clause = exemplar_for(archetype, disease_area)
    if clause is None:
        return structural
    return f"{structural} For illustration, {clause}"


def classify_archetype(
    dimensions: Dimensions,
    upstream_node_carries_signal: bool = False,
    disease_area: Optional[str] = None,
) -> tuple[Archetype, str]:
    """Map the dimension vector to a structural position label + rationale.

    `upstream_node_carries_signal` is a real pathway fact that must be passed in;
    it cannot be derived from the target's own evidence, which is precisely why a
    displaced signal is invisible without it. `disease_area` only picks the
    illustration and never changes the returned archetype.
    """
    assoc = _tier(dimensions, Dimension.ASSOCIATION)
    gen = _tier(dimensions, Dimension.GENETIC)
    interv = _tier(dimensions, Dimension.INTERVENTION)
    temp = _tier(dimensions, Dimension.TEMPORAL)
    med = _tier(dimensions, Dimension.MEDIATION)
    gen_bidirectional = _genetic_is_bidirectional(dimensions)

    strong_assoc = assoc in (Tier.STRONG, Tier.MODERATE)
    genetic_causal = gen in _SUPPORTIVE

    # 1. Validated driver: bidirectional causal control + strong successful
    #    intervention. Checked first; a MODERATE intervention falls through to
    #    initiator (correlation decayed, intervention only partially effective).
    if gen_bidirectional and interv == Tier.STRONG:
        archetype = Archetype.VALIDATED_DRIVER

    # 2. Upstream initiator: strong genetics, weak concurrent correlation. The
    #    weak association is the tell, not a strike against it.
    elif gen == Tier.STRONG and assoc in _WEAKISH and interv != Tier.CONTRADICTED:
        archetype = Archetype.UPSTREAM_INITIATOR

    # 3. Displaced signal: only detectable WITH pathway context. Strong
    #    association, the target's own genetics null/weak, and a neighbour carries
    #    the signal. Without the flag this is indistinguishable from a plain marker.
    elif upstream_node_carries_signal and strong_assoc and gen in (
        Tier.CONTRADICTED,
        Tier.WEAK,
        Tier.ABSENT,
    ):
        archetype = Archetype.DISPLACED_SIGNAL

    # 4. Downstream mediator: strong association + a mediating position, weak
    #    independent genetics. Checked BEFORE the marker rule -- a mediator IS
    #    causal, and must not be flattened into "just a marker".
    elif strong_assoc and med in _SUPPORTIVE and gen in _WEAKISH:
        archetype = Archetype.DOWNSTREAM_MEDIATOR

    # 5. Reactive consequence: the node moves only after onset (temporal evidence
    #    points the wrong way in time).
    elif temp == Tier.CONTRADICTED:
        archetype = Archetype.REACTIVE_CONSEQUENCE

    # 6. Associated non-causal marker: strong association, null/contradicted
    #    genetics, no successful intervention, no mediating role.
    elif strong_assoc and gen in (Tier.CONTRADICTED, Tier.WEAK, Tier.ABSENT) and interv in (
        Tier.CONTRADICTED,
        Tier.WEAK,
        Tier.ABSENT,
    ):
        archetype = Archetype.ASSOCIATED_NONCAUSAL

    # 7. Fallback: genetic/interventional support exists but does not fit a named
    #    shape cleanly -> treat as a genetically-supported causal node.
    elif genetic_causal or interv in _SUPPORTIVE:
        archetype = Archetype.UPSTREAM_INITIATOR

    # 8. Nothing causal or associational on record.
    else:
        archetype = Archetype.UNTESTED

    return archetype, _build_rationale(archetype, disease_area)
