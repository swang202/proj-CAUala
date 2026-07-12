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
