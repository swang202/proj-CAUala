"""
End-to-end pipeline tests. The known-answer scoring tests lock the pure functions;
these lock the whole retrieval -> assemble -> gate -> classify -> appraise path,
plus the non-negotiable invariants (build-brief section 9) at the pipeline level.
"""

from __future__ import annotations

import pytest

from src.orchestrator import Orchestrator
from src.question import EdgeType, Node, NodeType, Question
from src.schema import Archetype, Composite, Dimension, Direction, Tier
from src.scoring_engine import assemble_dimension
from src.validation import run_validation


@pytest.fixture(scope="module")
def orch() -> Orchestrator:
    return Orchestrator(online=False)


def _q(target: str, disease: str) -> Question:
    return Question(
        source=Node(type=NodeType.GENE, symbol=target),
        target=Node(type=NodeType.DISEASE, symbol=disease),
        edge_type=EdgeType.CAUSAL_RISK,
    )


@pytest.mark.parametrize(
    "target,disease,archetype,composite",
    [
        ("PCSK9", "coronary artery disease", Archetype.VALIDATED_DRIVER, Composite.CAUSAL_DRIVER),
        ("HDL-C", "coronary artery disease", Archetype.ASSOCIATED_NONCAUSAL, Composite.REFUTED),
        ("CRP", "coronary artery disease", Archetype.DISPLACED_SIGNAL, Composite.LIKELY_NONCAUSAL),
        ("APP/amyloid", "Alzheimer's disease", Archetype.UPSTREAM_INITIATOR, Composite.LIKELY_CAUSAL),
        ("tau", "Alzheimer's disease", Archetype.DOWNSTREAM_MEDIATOR, Composite.PLAUSIBLE),
    ],
)
def test_pipeline_recovers_known_answers(orch, target, disease, archetype, composite):
    ap = orch.appraise_sync(_q(target, disease))
    assert ap.archetype == archetype
    assert ap.composite == composite


def test_pipeline_posterior_respects_gate_for_every_case(orch):
    """Invariant #8 at the pipeline boundary."""
    for case in orch.fixtures.all_cases():
        ap = orch.appraise_sync(_q(case.target, case.disease))
        assert ap.posterior_respects_gate()
        # And pre-calibration the render never leaks a bare float.
        assert "uncalibrated" in ap.posterior.render()


def test_pipeline_surfaces_conflict_not_average(orch):
    """Invariant #5: HDL's directional association vs null genetics is surfaced."""
    ap = orch.appraise_sync(_q("HDL-C", "coronary artery disease"))
    assert ap.conflicts
    assert any("not averaged" in c or "causal reading" in c for c in ap.conflicts)


def test_displaced_signal_needs_pathway_context(orch):
    """CRP is a displaced_signal only because the case records the upstream fact.
    Strip it and the same evidence reads as a plain marker."""
    ap_with = orch.appraise_sync(_q("CRP", "coronary artery disease"))
    assert ap_with.archetype == Archetype.DISPLACED_SIGNAL

    # Re-run classification with the pathway flag off: reverts to plain marker.
    from src.scoring import classify_archetype

    dims = ap_with.dimensions
    arch_off, _ = classify_archetype(dims, upstream_node_carries_signal=False)
    assert arch_off == Archetype.ASSOCIATED_NONCAUSAL


def test_directionless_item_cannot_set_causal_tier():
    """Invariant #1: a cross-sectional (direction-less) item cannot lift a causal
    dimension above WEAK."""
    from src.schema import EvidenceItem, EvidenceType, Readout, System

    item = EvidenceItem(
        id="xsec",
        target="X",
        disease="Y",
        dimension=Dimension.GENETIC,
        evidence_type=EvidenceType.CROSS_SECTIONAL,
        direction=Direction.UP_HARMS,
        system=System.HUMAN,
        readout=Readout.MOLECULAR_PROFILE,
        source="PMID:1",
        provenance_group="g1",
    )
    assessed = assemble_dimension(Dimension.GENETIC, [item])
    assert assessed.tier == Tier.WEAK


def test_dedup_by_provenance_group():
    """Ten records citing one observation count once."""
    from src.schema import EvidenceItem, EvidenceType, Readout, System

    items = [
        EvidenceItem(
            id=f"r{i}",
            target="X",
            disease="Y",
            dimension=Dimension.GENETIC,
            evidence_type=EvidenceType.MENDELIAN_RANDOMIZATION,
            direction=Direction.UP_HARMS,
            system=System.HUMAN,
            readout=Readout.CLINICAL_OUTCOME,
            source="PMID:1",
            provenance_group="same_observation",
        )
        for i in range(10)
    ]
    assessed = assemble_dimension(Dimension.GENETIC, items)
    assert len(assessed.items) == 1


def test_validation_harness_recovers_and_separates():
    report = run_validation()
    assert report.all_recovered, report.summary()
    assert report.separation_holds, report.summary()
