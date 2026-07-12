"""
Open Targets Platform connector (the integrated backbone + benchmark).

Real GraphQL against api.platform.opentargets.org/api/v4/graphql (keyless).
Two capabilities:

  * `resolve` -- free-text -> ontology id (target Ensembl / disease MONDO-EFO),
    used as the ONLINE harmonizer when the offline table misses;
  * `fetch`   -- the integrated target<->disease association score, mapped to a
    single DIRECTION-LESS association EvidenceItem.

Open Targets already integrates L2G, fine-mapping and colocalization into one
score; CAUala's value is the causal re-scoring on top, so this connector never
emits a causal tier by itself -- the score carries no direction and, per the
directionality gate, contributes to strength/consistency only. A network failure
degrades to [] (a named gap), never a crash.
"""

from __future__ import annotations

from typing import Optional

from src.question import NodeType, Question
from src.schema import (
    Dimension,
    Direction,
    EffectSize,
    EvidenceItem,
    EvidenceType,
    Readout,
    System,
)

API_URL = "https://api.platform.opentargets.org/api/v4/graphql"

# Resolve free text to the top target/disease entity id.
_SEARCH_QUERY = """
query Resolve($s: String!, $entities: [String!]!) {
  search(queryString: $s, entityNames: $entities) {
    hits { id name entity }
  }
}
"""

# Integrated association score for a specific (target, disease) pair. `Bs` filters
# the target's associated diseases down to the one asked about.
_ASSOCIATION_QUERY = """
query Assoc($ensemblId: String!, $diseaseIds: [String!]) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    associatedDiseases(Bs: $diseaseIds) {
      count
      rows {
        disease { id name }
        score
        datatypeScores { id score }
      }
    }
  }
}
"""


def _post(query: str, variables: dict, timeout: float, attempts: int = 3) -> Optional[dict]:
    """POST with small exponential backoff; returns None on persistent failure."""
    import time

    import httpx

    for i in range(attempts):
        try:
            resp = httpx.post(API_URL, json={"query": query, "variables": variables}, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                return None
            return data.get("data")
        except Exception:
            if i == attempts - 1:
                return None
            time.sleep(0.5 * (i + 1))
    return None


class OpenTargetsConnector:
    connector_id = "opentargets"
    modality = "integrated_backbone"

    def __init__(self, online: bool = False, timeout: float = 20.0) -> None:
        self.online = online
        self.timeout = timeout

    # -- online id resolution (harmonizer fallback) -------------------------

    def resolve(self, text: str, kind: str) -> Optional[tuple[str, str]]:
        """Resolve free text to (id, canonical_name). `kind` is 'target' or
        'disease'. Returns None offline or on miss."""
        if not self.online:
            return None
        data = _post(_SEARCH_QUERY, {"s": text, "entities": [kind]}, self.timeout)
        if not data:
            return None
        hits = [h for h in data.get("search", {}).get("hits", []) if h["entity"] == kind]
        if not hits:
            return None
        return hits[0]["id"], hits[0]["name"]

    # -- association fetch --------------------------------------------------

    def available_for(self, q: Question) -> bool:
        return (
            self.online
            and q.source.type in (NodeType.GENE, NodeType.VARIANT, NodeType.PROTEIN)
            and q.target.type in (NodeType.DISEASE, NodeType.PHENOTYPE)
            and (q.source.id or "").startswith("ENSG")
            and q.target.id is not None
        )

    def _assoc_rows(self, ensembl_id: str, disease_id: str) -> list[dict]:
        data = _post(
            _ASSOCIATION_QUERY,
            {"ensemblId": ensembl_id, "diseaseIds": [disease_id]},
            self.timeout,
        )
        if not data:
            return []
        return data.get("target", {}).get("associatedDiseases", {}).get("rows", []) or []

    async def fetch(self, q: Question) -> list[EvidenceItem]:
        if not self.available_for(q):
            return []
        rows = self._assoc_rows(q.source.id, q.target.id)
        # OT's association index keys on ONE ontology id. An EFO id resolved
        # offline may miss where OT indexes under MONDO (or vice versa). If the
        # direct query is empty, re-resolve the disease via OT's own search and
        # retry with the id OT actually indexes -- self-correcting harmonization.
        if not rows:
            hit = self.resolve(q.target.label or q.target.display(), "disease")
            if hit and hit[0] != q.target.id:
                rows = self._assoc_rows(q.source.id, hit[0])
        if not rows:
            return []
        row = rows[0]
        score = float(row.get("score", 0.0))
        by_type = {d["id"]: round(float(d["score"]), 3) for d in row.get("datatypeScores", [])}
        return [
            EvidenceItem(
                id=f"ot_{q.source.id}_{q.target.id}",
                target=q.source.symbol or q.source.id or "target",
                disease=q.target.label or q.target.id or "disease",
                dimension=Dimension.ASSOCIATION,
                evidence_type=EvidenceType.OBSERVATIONAL_COHORT,
                direction=Direction.NULL,  # integrated score carries no direction
                effect=EffectSize(value=round(score, 3), units="OT association score (0-1)"),
                system=System.HUMAN,
                readout=Readout.MOLECULAR_PROFILE,
                falsified_by=["Open Targets association score falls to ~0 on reingest"],
                source="10.1093/nar/gkac1046",  # Open Targets Platform 2023 NAR
                provenance_group=f"opentargets_{q.source.id}",
                notes=(
                    "Integrated backbone score only. Direction-less by construction; "
                    "contributes to strength/consistency, never a causal tier. "
                    f"datatype scores: {by_type}"
                ),
            )
        ]
