"""
KnowledgeConnector -- the model-in-the-loop evidence source, with a hard
citation-verification gate.

Why this exists. The wired structured databases (Open Targets, gnomAD) are only as
good as their machine-readable annotations. For a locus like APOE the association is
overwhelming, yet Open Targets returns the genetic records with no direction-of-effect
field, so the directional connector drops them and the gene under-calls to
`unvalidated`. A model *knows* the established fact (APOE-e4 raises Alzheimer risk,
Corder 1993) -- but a model is also exactly the thing that manufactures a plausible
citation. So the discipline of the whole tool applies here in its sharpest form:

    the model PROPOSES cited evidence; it never decides the verdict.

Every claim the model returns is put through two gates before it may enter the ledger:

  1. EXISTENCE + TOPICALITY -- the proposed PMID is looked up live in Europe PMC
     (keyless). It must resolve to a real record whose title/abstract actually
     mentions the gene (or a supplied synonym) AND the disease. A hallucinated PMID
     fails existence; a real-but-off-topic PMID (the classic "plausible but wrong"
     failure) fails topicality. Only survivors become EvidenceItems.

  2. DETERMINISTIC SCORING -- survivors are handed to the same
     `assemble_dimension` scorer as every other connector. The model's prose never
     touches a tier; it only supplies a direction/effect/citation that the scorer
     weighs exactly as it would an Open Targets record.

Provenance is tagged `[TRAINING - verify]`: the claim is model-proposed and its
citation was confirmed to exist and match topic, but the effect size still has to be
read in the primary paper before anyone relies on it. Nothing here is presented as a
checked fact.

Enablement is explicit opt-in (`CAUALA_ENABLE_KNOWLEDGE=1` + an API key), so no
appraisal makes a model call -- or incurs cost -- unless the operator asked for it.
When disabled or unconfigured the connector reports itself as a named gap and returns
`[]`, never a crash.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable

import httpx

from src.question import NodeType, Question
from src.schema import EffectSize, EvidenceItem

_EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# The vocabularies the model must map into. Kept here (not imported as enums) so the
# proposer prompt can enumerate the exact allowed strings and we can reject anything
# off-vocabulary before the schema does.
_DIMENSIONS = ["intervention", "genetic", "temporal", "mediation", "mechanism",
               "association", "robustness"]
_DIRECTIONS = ["target_up_disease_up", "target_down_disease_down",
               "target_up_disease_down", "target_down_disease_up", "null"]
_EVIDENCE_TYPES = ["human_rct", "human_cell_perturbation", "animal_perturbation",
                   "rare_penetrant_variant", "protective_allele", "allelic_series",
                   "mendelian_randomization", "gwas_colocalization", "gwas_nearest_gene",
                   "longitudinal_cohort", "anchored_onset_cohort", "formal_mediation",
                   "pathway_epistasis", "biochemical_pathway", "expression_concordance",
                   "cross_sectional", "observational_cohort", "replication",
                   "sensitivity_analysis"]
_SYSTEMS = ["human", "human_primary_cell", "human_derived_model", "animal_model",
            "cell_line", "in_silico"]
_READOUTS = ["clinical_outcome", "surrogate_endpoint", "disease_pathology",
             "biomarker", "molecular_profile", "cellular_phenotype"]


# --------------------------------------------------------------------------- #
# The model's output shape
# --------------------------------------------------------------------------- #
@dataclass
class ProposedClaim:
    """One candidate piece of evidence proposed by the model, pre-verification.

    `gene_terms` / `disease_terms` are the surface forms (synonyms) the model
    expects to find in the cited paper's title/abstract -- e.g. APOE ->
    ['apolipoprotein e', 'apoe']. They are what the topicality gate matches on,
    because a real paper's title often carries the protein name, not the symbol.
    """

    gene: str
    disease: str
    dimension: str
    direction: str
    evidence_type: str
    system: str
    readout: str
    pmid: str
    claim: str
    gene_terms: list[str] = field(default_factory=list)
    disease_terms: list[str] = field(default_factory=list)
    effect_value: Optional[float] = None
    effect_units: Optional[str] = None
    effect_ci_low: Optional[float] = None
    effect_ci_high: Optional[float] = None
    assumptions_required: list[str] = field(default_factory=list)

    def vocabulary_ok(self) -> bool:
        return (
            self.dimension in _DIMENSIONS
            and self.direction in _DIRECTIONS
            and self.evidence_type in _EVIDENCE_TYPES
            and self.system in _SYSTEMS
            and self.readout in _READOUTS
        )

    def normalized_pmid(self) -> Optional[str]:
        raw = str(self.pmid).strip().upper().replace("PMID:", "").strip()
        return raw if raw.isdigit() else None


@runtime_checkable
class Proposer(Protocol):
    """Anything that turns a Question into candidate cited claims. The API-backed
    proposer is the default; a StaticProposer serves tests and offline knowledge
    packs. Either way its output is untrusted until the connector verifies it."""

    def propose(self, q: Question) -> list[ProposedClaim]: ...


# --------------------------------------------------------------------------- #
# Proposers
# --------------------------------------------------------------------------- #
class StaticProposer:
    """A proposer backed by a fixed in-memory table keyed by (gene, disease)
    lowercased. Used by the test suite and as a way to ship a small hand-checked
    knowledge pack without any model call. Same untrusted status as the model: its
    claims still go through the citation gate."""

    def __init__(self, table: dict[tuple[str, str], list[ProposedClaim]]) -> None:
        self._table = {(g.lower(), d.lower()): v for (g, d), v in table.items()}

    def propose(self, q: Question) -> list[ProposedClaim]:
        key = (q.source.display().lower(), q.target.display().lower())
        return list(self._table.get(key, []))


_PROPOSER_SYSTEM = (
    "You are an evidence *proposer* for a causal-appraisal tool, not its judge. "
    "Given a gene/protein and a disease, return only WELL-ESTABLISHED causal-evidence "
    "facts that each rest on a REAL primary-literature paper you are confident exists, "
    "and for which you can give the correct PubMed ID. You are proposing candidates that "
    "a separate program will verify against Europe PMC and then score deterministically; "
    "your prose never sets the verdict. Rules: (1) never invent or guess a PMID -- if you "
    "are not confident a real PMID exists for a claim, omit that claim entirely; (2) prefer "
    "the original observation over reviews; (3) give the direction and, when known, an effect "
    "size with units; (4) supply gene_terms and disease_terms as the surface forms (including "
    "protein names and common abbreviations) that would actually appear in that paper's title "
    "or abstract, since verification matches on them; (5) return at most 6 claims; (6) if you "
    "have no high-confidence cited fact, return an empty list. Better to return nothing than "
    "anything unverifiable."
)

_SUBMIT_TOOL = {
    "name": "submit_evidence",
    "description": "Submit the proposed cited evidence claims.",
    "input_schema": {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "dimension": {"type": "string", "enum": _DIMENSIONS},
                        "direction": {"type": "string", "enum": _DIRECTIONS},
                        "evidence_type": {"type": "string", "enum": _EVIDENCE_TYPES},
                        "system": {"type": "string", "enum": _SYSTEMS},
                        "readout": {"type": "string", "enum": _READOUTS},
                        "pmid": {"type": "string"},
                        "claim": {"type": "string"},
                        "gene_terms": {"type": "array", "items": {"type": "string"}},
                        "disease_terms": {"type": "array", "items": {"type": "string"}},
                        "effect_value": {"type": ["number", "null"]},
                        "effect_units": {"type": ["string", "null"]},
                        "effect_ci_low": {"type": ["number", "null"]},
                        "effect_ci_high": {"type": ["number", "null"]},
                        "assumptions_required": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["dimension", "direction", "evidence_type", "system",
                                 "readout", "pmid", "claim", "gene_terms", "disease_terms"],
                },
            }
        },
        "required": ["claims"],
    },
}


class AnthropicProposer:
    """Live proposer backed by the Claude Messages API. Forces a single structured
    tool call so the output is already vocabulary-constrained. Any failure (missing
    key, missing package, network, malformed output) raises; the connector catches it
    and degrades to a named gap."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.model = model or os.environ.get("CAUALA_KNOWLEDGE_MODEL", "claude-sonnet-5")
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def propose(self, q: Question) -> list[ProposedClaim]:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        import anthropic  # lazy: only needed when the connector is enabled

        client = anthropic.Anthropic(api_key=self.api_key)
        user = (
            f"Gene/protein: {q.source.display()}\n"
            f"Disease: {q.target.display()}\n"
            f"Relationship asked: does the gene/protein causally influence the disease?\n"
            "Propose the established, citable causal-evidence facts."
        )
        msg = client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=_PROPOSER_SYSTEM,
            tools=[_SUBMIT_TOOL],
            tool_choice={"type": "tool", "name": "submit_evidence"},
            messages=[{"role": "user", "content": user}],
        )
        payload = None
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use":
                payload = block.input
                break
        if not payload:
            return []
        if isinstance(payload, str):
            payload = json.loads(payload)
        return [
            ProposedClaim(
                gene=q.source.display(),
                disease=q.target.display(),
                dimension=c.get("dimension", ""),
                direction=c.get("direction", ""),
                evidence_type=c.get("evidence_type", ""),
                system=c.get("system", ""),
                readout=c.get("readout", ""),
                pmid=str(c.get("pmid", "")),
                claim=c.get("claim", ""),
                gene_terms=[t.lower() for t in c.get("gene_terms", [])],
                disease_terms=[t.lower() for t in c.get("disease_terms", [])],
                effect_value=c.get("effect_value"),
                effect_units=c.get("effect_units"),
                effect_ci_low=c.get("effect_ci_low"),
                effect_ci_high=c.get("effect_ci_high"),
                assumptions_required=c.get("assumptions_required", []),
            )
            for c in payload.get("claims", [])
        ]


# --------------------------------------------------------------------------- #
# The citation gate
# --------------------------------------------------------------------------- #
@dataclass
class VerificationResult:
    ok: bool
    reason: str
    title: str = ""


def _verify_citation(
    pmid: str, gene_terms: list[str], disease_terms: list[str],
    client: Optional[httpx.Client] = None,
) -> VerificationResult:
    """Confirm the PMID resolves to a real Europe PMC record whose title+abstract
    mentions the gene AND the disease. This is what stops a hallucinated or
    off-topic citation from entering the ledger."""
    own = client is None
    client = client or httpx.Client(timeout=20)
    try:
        r = client.get(_EUROPEPMC, params={
            "query": f"EXT_ID:{pmid} AND SRC:MED",
            "format": "json", "resultType": "core",
        })
        hits = r.json().get("resultList", {}).get("result", [])
    except Exception as exc:  # network/parse -- treat as unverifiable, do not crash
        return VerificationResult(False, f"lookup failed: {exc}")
    finally:
        if own:
            client.close()

    if not hits:
        return VerificationResult(False, "PMID not found in Europe PMC")
    h = hits[0]
    title = h.get("title", "") or ""
    text = f"{title} {h.get('abstractText', '') or ''}".lower()
    gene_ok = any(t.lower() in text for t in gene_terms if t)
    dis_ok = any(t.lower() in text for t in disease_terms if t)
    if not gene_ok:
        return VerificationResult(False, "citation does not mention the gene", title[:90])
    if not dis_ok:
        return VerificationResult(False, "citation does not mention the disease", title[:90])
    return VerificationResult(True, "verified", title[:90])


# --------------------------------------------------------------------------- #
# The connector
# --------------------------------------------------------------------------- #
class KnowledgeConnector:
    """Model-proposed, citation-verified evidence. Implements the BaseConnector
    contract. `dropped` records why each rejected claim was rejected, so the
    orchestrator can surface it as a named gap rather than hide it."""

    connector_id = "knowledge"
    modality = "literature_knowledge"

    def __init__(self, proposer: Optional[Proposer] = None, enabled: bool = True) -> None:
        self.proposer = proposer
        self.enabled = enabled and proposer is not None
        self.dropped: list[str] = []

    @classmethod
    def from_env(cls) -> "KnowledgeConnector":
        """Build the live connector iff explicitly opted in AND an API key exists.
        Otherwise a disabled connector that returns [] and reports a named gap."""
        opted_in = os.environ.get("CAUALA_ENABLE_KNOWLEDGE", "").lower() in ("1", "true", "yes")
        has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
        if opted_in and has_key:
            return cls(proposer=AnthropicProposer(), enabled=True)
        return cls(proposer=None, enabled=False)

    def available_for(self, q: Question) -> bool:
        if not self.enabled:
            return False
        return (
            q.source.type in (NodeType.GENE, NodeType.PROTEIN, NodeType.VARIANT)
            and q.target.type == NodeType.DISEASE
        )

    async def fetch(self, q: Question) -> list[EvidenceItem]:
        self.dropped = []
        if not self.enabled or self.proposer is None:
            return []
        try:
            claims = self.proposer.propose(q)
        except Exception as exc:  # degrade gracefully -- never crash an appraisal
            self.dropped.append(f"proposer unavailable: {exc}")
            return []

        items: list[EvidenceItem] = []
        seen_pmids: set[str] = set()
        with httpx.Client(timeout=20) as client:
            for i, c in enumerate(claims):
                if not c.vocabulary_ok():
                    self.dropped.append(f"{c.pmid}: off-vocabulary field")
                    continue
                pmid = c.normalized_pmid()
                if not pmid:
                    self.dropped.append(f"{c.pmid!r}: not a numeric PMID")
                    continue
                gene_terms = c.gene_terms or [c.gene]
                disease_terms = c.disease_terms or [c.disease]
                v = _verify_citation(pmid, gene_terms, disease_terms, client=client)
                if not v.ok:
                    self.dropped.append(f"PMID:{pmid}: {v.reason}")
                    continue
                if pmid in seen_pmids:
                    continue  # one paper is one piece of evidence
                seen_pmids.add(pmid)
                items.append(self._to_item(q, c, pmid, v.title, i))
        return items

    def _to_item(self, q: Question, c: ProposedClaim, pmid: str, title: str, i: int) -> EvidenceItem:
        effect = None
        if c.effect_value is not None and c.effect_units:
            effect = EffectSize(
                value=c.effect_value, units=c.effect_units,
                ci_low=c.effect_ci_low, ci_high=c.effect_ci_high,
            )
        note = (
            f"Model-proposed from established literature; citation confirmed in Europe PMC "
            f"(\"{title}\") to mention the gene and disease. READ THE PRIMARY PAPER to confirm "
            f"the effect and direction before use. Claim: {c.claim}"
        )
        return EvidenceItem(
            id=f"knowledge-{q.source.display()}-{pmid}-{i}",
            target=q.source.display(),
            disease=q.target.display(),
            dimension=c.dimension,
            evidence_type=c.evidence_type,
            direction=c.direction,
            effect=effect,
            system=c.system,
            readout=c.readout,
            assumptions_required=c.assumptions_required,
            falsified_by=[],
            source=f"PMID:{pmid}",
            provenance_group=f"knowledge:{pmid}",
            contradicts=[],
            notes=note,
        )
