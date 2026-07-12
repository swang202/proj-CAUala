"""
Open Targets Platform connector (the integrated backbone + benchmark).

Real GraphQL against api.platform.opentargets.org (keyless). Used only when the
orchestrator runs in --online mode; offline it reports unavailable and the
FixtureConnector serves instead. Open Targets already integrates L2G,
fine-mapping and colocalization; CAUala's value is the causal RE-scoring on top,
so this connector maps the association score into direction-less association
evidence and lets the deterministic scorer decide what causal weight it carries.

Network access is wrapped so a failure degrades to [] (a named gap), never a
crash. The GraphQL query is kept explicit so it is auditable.
"""

from __future__ import annotations

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

# Association-score query by Ensembl gene id + EFO/MONDO disease id.
_ASSOCIATION_QUERY = """
query TargetDisease($ensemblId: String!, $efoId: String!) {
  disease(efoId: $efoId) {
    id
    name
    associatedTargets(page: {index: 0, size: 1}, BFilter: $ensemblId) {
      rows {
        target { id approvedSymbol }
        score
        datatypeScores { id score }
      }
    }
  }
}
"""


class OpenTargetsConnector:
    """Fetches the Open Targets integrated association score for a
    gene->disease question and maps it to a single, direction-less
    association EvidenceItem (backbone / benchmark, never a causal tier by itself)."""

    connector_id = "opentargets"
    modality = "integrated_backbone"

    def __init__(self, online: bool = False, timeout: float = 20.0) -> None:
        self.online = online
        self.timeout = timeout

    def available_for(self, q: Question) -> bool:
        return (
            self.online
            and q.source.type in (NodeType.GENE, NodeType.VARIANT)
            and q.target.type in (NodeType.DISEASE, NodeType.PHENOTYPE)
            and q.source.is_resolved()
            and q.target.is_resolved()
        )

    async def fetch(self, q: Question) -> list[EvidenceItem]:
        if not self.available_for(q):
            return []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    API_URL,
                    json={
                        "query": _ASSOCIATION_QUERY,
                        "variables": {"ensemblId": q.source.id, "efoId": q.target.id},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            # Degrade to a named gap; the orchestrator records it in not_examined.
            return []

        rows = (
            data.get("data", {})
            .get("disease", {})
            .get("associatedTargets", {})
            .get("rows", [])
        )
        if not rows:
            return []
        row = rows[0]
        score = float(row.get("score", 0.0))
        return [
            EvidenceItem(
                id=f"ot_{q.source.id}_{q.target.id}",
                target=q.source.symbol or q.source.id or "target",
                disease=q.target.label or q.target.id or "disease",
                dimension=Dimension.ASSOCIATION,
                evidence_type=EvidenceType.OBSERVATIONAL_COHORT,
                direction=Direction.NULL,  # integrated score carries no direction
                effect=EffectSize(value=score, units="OT association score (0-1)"),
                system=System.HUMAN,
                readout=Readout.MOLECULAR_PROFILE,
                falsified_by=["Open Targets association score falls to ~0 on reingest"],
                # Open Targets is a database of record; cite the platform DOI.
                source="10.1093/nar/gkac1046",  # TODO:cite -- Open Targets Platform 2023 NAR
                provenance_group=f"opentargets_{q.source.id}",
                notes=(
                    "Integrated backbone score only. Direction-less by construction; "
                    "contributes to strength/consistency, never to a causal tier."
                ),
            )
        ]
