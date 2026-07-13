"""
Opt-in live smoke tests against real databases. Skipped by default so the normal
suite runs fully offline on recorded fixtures (per the brief). Enable with:

    CAUALA_LIVE=1 .venv/bin/python -m pytest tests/test_live.py -v

These hit the public, keyless Open Targets and gnomAD APIs.
"""

from __future__ import annotations

import asyncio
import os

import pytest

from src.orchestrator import Orchestrator
from src.question import EdgeType, Node, NodeType, Question
from src.schema import Dimension, Direction

LIVE = os.getenv("CAUALA_LIVE") == "1"
pytestmark = pytest.mark.skipif(not LIVE, reason="set CAUALA_LIVE=1 to run live network tests")


def _q(sym: str, dis: str) -> Question:
    return Question(
        source=Node(type=NodeType.GENE, symbol=sym),
        target=Node(type=NodeType.DISEASE, symbol=dis),
        edge_type=EdgeType.CAUSAL_RISK,
    )


def test_opentargets_resolves_and_scores_uncurated_target():
    """A target NOT in the curated store resolves from scratch and returns a live
    Open Targets score, but the direction-less backbone alone cannot make it causal."""
    orch = Orchestrator(online=True)
    ap = orch.appraise_sync(_q("SORT1", "coronary artery disease"))
    assoc = ap.dimensions.get(Dimension.ASSOCIATION)
    assert assoc is not None and assoc.items, "expected a live Open Targets association item"
    # No directional causal evidence -> the integrated score cannot lift the tier.
    assert ap.composite.value in ("unvalidated", "plausible", "likely_noncausal")


def test_opentargets_self_corrects_efo_mondo_mismatch():
    """An offline-resolved EFO id that OT indexes under MONDO must still return a
    score via the connector's search-retry fallback."""
    orch = Orchestrator(online=True)
    q = orch._resolve_online(_q("SORT1", "coronary artery disease"))
    items = asyncio.run(orch.opentargets.fetch(q))
    assert items, "self-correcting disease-id retry should recover the score"
    assert 0.0 <= items[0].effect.value <= 1.0


def test_resolver_guess_ask_notfound():
    """The guess -> ask -> not-found decision on messy real input."""
    from src.resolve import EntityResolver
    from src.question import NodeType

    r = EntityResolver(online=True)
    # confident guesses (type-constrained + alias layer)
    assert r.resolve("PD", [NodeType.DISEASE]).best.id == "MONDO_0005180"
    assert r.resolve("MS", [NodeType.DISEASE]).best.name.lower() == "multiple sclerosis"
    assert r.resolve("LRRK2", [NodeType.GENE]).best.id == "ENSG00000188906"
    # garbage is rejected, not silently mis-resolved
    assert r.resolve("XYZ", [NodeType.DISEASE]).status == "not_found"
    # a protein-change mutation is now first-class: G2019S -> the variant, plus the
    # parent gene offered as the alternative for the picker.
    res = r.resolve("LRRK2 G2019S", [NodeType.VARIANT])
    assert res.status == "ambiguous"
    assert res.best.entity == "variant" and res.best.id == "12_40340400_G_A"
    assert any(c.entity == "target" for c in res.candidates)


def test_variant_question_is_first_class():
    """LRRK2 G2019S -> PD runs a variant-level appraisal from real evidence."""
    from src.orchestrator import Orchestrator
    from src.question import EdgeType, Node, NodeType, Question

    q = Question(
        source=Node(type=NodeType.VARIANT, symbol="LRRK2 G2019S"),
        target=Node(type=NodeType.DISEASE, symbol="PD"),
        edge_type=EdgeType.GENETIC_RISK,
    )
    ap = Orchestrator(online=True).appraise_sync(q)
    # the genetic dimension was populated from the variant's own evidence
    assert Dimension.GENETIC in ap.dimensions
    assert ap.composite.value in ("plausible", "likely_causal", "causal_driver")


def test_gnomad_constraint_is_plausibility_only():
    """gnomAD constraint lands in the mechanism dimension and cannot raise the tier."""
    orch = Orchestrator(online=True)
    q = orch._resolve_online(_q("PCSK9", "coronary artery disease"))
    assert orch.gnomad.available_for(q)
    fetched = asyncio.run(orch.gnomad.fetch(q))
    if not fetched:
        pytest.skip("gnomAD momentarily unavailable/rate-limited (retries exhausted)")
    assert fetched[0].dimension == Dimension.MECHANISM
    assert fetched[0].direction == Direction.NULL
