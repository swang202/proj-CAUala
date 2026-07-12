"""
Disease-area-keyed exemplars for archetype rationales.

The separation invariant (tests/test_known_answers.py): a rationale is a
STRUCTURAL sentence (disease-agnostic, complete on its own) optionally followed
by a "For illustration, ..." clause drawn from a disease area. The structural
part must stand alone -- stripping the exemplar must not leave an unintelligible
sentence, and must never leak a disease-specific token (HDL, tau, amyloid, ...)
into logic that is supposed to be disease-agnostic.

`exemplar_for` returns only the illustration clause (or None). The structural
rationales live in `scoring.py`. A cancer researcher must never be told their
target has "the tau pattern": if a disease area is named, its own illustration is
used; UNTESTED has no exemplar by construction.
"""

from __future__ import annotations

from typing import Optional

from src.schema import Archetype


# For each archetype, a table of disease-area -> illustration clause. The
# "_default" key is used when no disease area is given or the area is unknown.
# Every clause is phrased to slot after "For illustration, ".
_EXEMPLARS: dict[Archetype, dict[str, str]] = {
    Archetype.VALIDATED_DRIVER: {
        "cardiovascular": (
            "PCSK9 in coronary disease -- loss-of-function alleles protect, "
            "gain-of-function causes familial hypercholesterolemia, and PCSK9 "
            "inhibitors cut events in outcome trials."
        ),
        "oncology": (
            "BCR-ABL in chronic myeloid leukemia and HER2 in breast cancer, "
            "where the driver lesion and a targeted agent against it both check out."
        ),
        "_default": (
            "PCSK9 in coronary disease, where protective and harmful alleles and a "
            "successful trial all converge on the same node."
        ),
    },
    Archetype.ASSOCIATED_NONCAUSAL: {
        "cardiovascular": (
            "HDL cholesterol in coronary disease -- decades of clean epidemiology, "
            "null Mendelian randomization, and three failed CETP-inhibitor trials."
        ),
        "oncology": (
            "beta-carotene, which tracked lower lung cancer risk across cohorts yet "
            "raised lung cancer incidence when given as a supplement in randomized trials."
        ),
        "_default": (
            "HDL cholesterol in coronary disease, a strong marker whose HDL-raising "
            "variants and drugs both failed to move outcomes."
        ),
    },
    Archetype.DISPLACED_SIGNAL: {
        "cardiovascular": (
            "CRP versus IL-6 in coronary disease -- CRP correlates but its variants "
            "are null, while the causal signal sits one node upstream at the IL-6 receptor."
        ),
        "_default": (
            "CRP versus IL-6 in coronary disease, where the measured marker is null "
            "but a neighbouring pathway node carries the causal signal."
        ),
    },
    Archetype.UPSTREAM_INITIATOR: {
        "neurology": (
            "amyloid in Alzheimer's disease -- bidirectional genetics, changes decades "
            "before symptoms, yet weak concurrent correlation with cognition."
        ),
        "cardiovascular": (
            "cumulative LDL exposure in coronary disease, where lifetime dose matters "
            "more than any single cross-sectional measurement."
        ),
        "_default": (
            "amyloid in Alzheimer's disease, an early node whose correlation with "
            "late disease severity has decayed with causal distance."
        ),
    },
    Archetype.DOWNSTREAM_MEDIATOR: {
        "neurology": (
            "tau in Alzheimer's disease -- it tracks cognitive decline better than "
            "amyloid because it sits closer to the effector end of the chain, not "
            "because it is more causal."
        ),
        "_default": (
            "tau in Alzheimer's disease, an excellent progression biomarker whose "
            "independent genetic support for the disease is weak."
        ),
    },
    Archetype.REACTIVE_CONSEQUENCE: {
        "_default": (
            "acute-phase reactants that rise only after disease onset and therefore "
            "cannot be driving what precedes them."
        ),
    },
    # UNTESTED intentionally has no exemplar: evidence of nothing illustrates nothing.
}


def exemplar_for(archetype: Archetype, disease_area: Optional[str] = None) -> Optional[str]:
    """Return an illustration clause for `archetype` in `disease_area`, or None.

    UNTESTED never has one. An unknown disease area falls back to `_default`, so
    the rationale is always complete but the archetype is never changed by the
    area (that invariance is enforced in scoring.classify_archetype).
    """
    if archetype == Archetype.UNTESTED:
        return None
    table = _EXEMPLARS.get(archetype)
    if not table:
        return None
    if disease_area:
        clause = table.get(disease_area.strip().lower())
        if clause is not None:
            return clause
    return table.get("_default")
