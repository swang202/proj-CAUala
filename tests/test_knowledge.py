"""
Tests for the model-in-the-loop KnowledgeConnector and its citation gate.

The point of the connector is that the model's claims are UNTRUSTED until their
citations are verified. These tests pin the two things that must never regress:

  * the connector is OFF unless explicitly opted in (no surprise model calls);
  * a claim whose PMID is missing or off-topic is DROPPED, not scored.

The offline tests drive the verifier with a fake HTTP client so the gate logic is
deterministic. The opt-in live test (CAUALA_LIVE=1) hits real Europe PMC and pins the
real-world behaviour that caught two hallucinated PMIDs during development.
"""

from __future__ import annotations

import asyncio
import os

import pytest

from src.connectors.knowledge import (
    KnowledgeConnector,
    ProposedClaim,
    StaticProposer,
    _verify_citation,
)
from src.question import EdgeType, Node, NodeType, Question


def _q(src="APOE", src_type=NodeType.GENE, tgt="Alzheimer disease", tgt_type=NodeType.DISEASE):
    return Question(source=Node(type=src_type, symbol=src),
                    target=Node(type=tgt_type, symbol=tgt),
                    edge_type=EdgeType.CAUSAL_RISK)


def _claim(pmid, gene_terms=("apolipoprotein e", "apoe"), disease_terms=("alzheimer",),
           dimension="genetic", direction="target_up_disease_up",
           evidence_type="allelic_series"):
    return ProposedClaim(
        gene="APOE", disease="Alzheimer disease", dimension=dimension, direction=direction,
        evidence_type=evidence_type, system="human", readout="clinical_outcome",
        pmid=pmid, claim="test", gene_terms=list(gene_terms), disease_terms=list(disease_terms),
    )


# --------------------------------------------------------------------------- #
# opt-in gating
# --------------------------------------------------------------------------- #
def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CAUALA_ENABLE_KNOWLEDGE", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    conn = KnowledgeConnector.from_env()
    assert conn.enabled is False
    assert conn.available_for(_q()) is False
    assert asyncio.run(conn.fetch(_q())) == []


def test_requires_both_optin_and_key(monkeypatch):
    monkeypatch.setenv("CAUALA_ENABLE_KNOWLEDGE", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert KnowledgeConnector.from_env().enabled is False  # opted in but no key


def test_available_for_scope_only_gene_to_disease():
    conn = KnowledgeConnector(proposer=StaticProposer({}), enabled=True)
    assert conn.available_for(_q()) is True
    assert conn.available_for(_q(tgt="TP53", tgt_type=NodeType.GENE)) is False   # gene->gene
    assert conn.available_for(_q(src="Alzheimer disease", src_type=NodeType.DISEASE)) is False  # disease->...


# --------------------------------------------------------------------------- #
# claim hygiene
# --------------------------------------------------------------------------- #
def test_vocabulary_and_pmid_normalisation():
    good = _claim("PMID:8346443")
    assert good.vocabulary_ok() is True
    assert good.normalized_pmid() == "8346443"
    assert _claim("not-a-pmid").normalized_pmid() is None
    bad = _claim("8346443", evidence_type="totally_made_up")
    assert bad.vocabulary_ok() is False


# --------------------------------------------------------------------------- #
# the citation gate (deterministic, fake HTTP)
# --------------------------------------------------------------------------- #
class _FakeResp:
    def __init__(self, payload): self._p = payload
    def json(self): return self._p


class _FakeClient:
    """Maps a PMID to a canned Europe PMC 'core' payload."""
    def __init__(self, by_pmid): self._by = by_pmid
    def get(self, url, params=None):
        pmid = params["query"].split("EXT_ID:")[1].split(" ")[0]
        result = self._by.get(pmid, [])
        return _FakeResp({"resultList": {"result": result}})


def _rec(title, abstract=""):
    return [{"title": title, "abstractText": abstract}]


def test_gate_keeps_ontopic_citation():
    client = _FakeClient({"8346443": _rec(
        "Gene dose of apolipoprotein E type 4 allele and the risk of Alzheimer's disease")})
    v = _verify_citation("8346443", ["apolipoprotein e", "apoe"], ["alzheimer"], client=client)
    assert v.ok is True


def test_gate_drops_missing_pmid():
    client = _FakeClient({})  # no record
    v = _verify_citation("99999999999", ["apoe"], ["alzheimer"], client=client)
    assert v.ok is False and "not found" in v.reason.lower()


def test_gate_drops_offtopic_citation():
    # a real PMID whose paper is about something else entirely
    client = _FakeClient({"9634822": _rec(
        "Virus-induced cell death in plants expressing the mammalian 2',5' oligoadenylate")})
    v = _verify_citation("9634822", ["apolipoprotein e", "apoe"], ["alzheimer"], client=client)
    assert v.ok is False and "gene" in v.reason.lower()


def test_gate_drops_gene_ok_but_disease_absent():
    client = _FakeClient({"111": _rec("Apolipoprotein E in cardiovascular lipid transport")})
    v = _verify_citation("111", ["apolipoprotein e"], ["alzheimer"], client=client)
    assert v.ok is False and "disease" in v.reason.lower()


def test_fetch_drops_bad_claims_and_dedupes(monkeypatch):
    """End-to-end fetch with the verifier patched: one good, one off-topic, one
    duplicate of the good one -> exactly one EvidenceItem, and `dropped` explains
    the reject."""
    from src.connectors import knowledge as kn

    good = _claim("8346443")
    offtopic = _claim("9634822")
    dup = _claim("8346443")  # same PMID as good -> deduped
    conn = KnowledgeConnector(
        proposer=StaticProposer({("APOE", "Alzheimer disease"): [good, offtopic, dup]}),
        enabled=True,
    )

    def fake_verify(pmid, gene_terms, disease_terms, client=None):
        from src.connectors.knowledge import VerificationResult
        if pmid == "8346443":
            return VerificationResult(True, "verified", "Gene dose of apolipoprotein E ...")
        return VerificationResult(False, "citation does not mention the gene")

    monkeypatch.setattr(kn, "_verify_citation", fake_verify)
    items = asyncio.run(conn.fetch(_q()))
    assert len(items) == 1
    assert items[0].source == "PMID:8346443"
    assert items[0].dimension.value == "genetic"
    assert any("9634822" in d for d in conn.dropped)


# --------------------------------------------------------------------------- #
# opt-in live test — real Europe PMC
# --------------------------------------------------------------------------- #
LIVE = os.getenv("CAUALA_LIVE") == "1"


@pytest.mark.skipif(not LIVE, reason="set CAUALA_LIVE=1 to run live network tests")
def test_apoe_gate_live():
    """Real Europe PMC: the true APOE paper verifies; a real-but-off-topic PMID
    (plant virus) is rejected. This is the guardrail that caught hallucinated PMIDs."""
    good = _verify_citation("8346443", ["apolipoprotein e", "apoe"], ["alzheimer"])
    assert good.ok is True
    plant = _verify_citation("9634822", ["apolipoprotein e", "apoe"], ["alzheimer"])
    assert plant.ok is False
