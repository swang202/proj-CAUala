"""
Open Targets variant-level connector -- makes a specific variant a first-class
question. Given a resolved variant (OT variant id, e.g. 12_40340400_G_A for LRRK2
G2019S) and a disease, it queries that variant's own disease evidence and maps the
disease-relevant rows into directional GENETIC EvidenceItems.

This is the variant analogue of the gene-level genetics connector: same direction
and effect mapping, but scoped to one variant rather than all of a gene's variants.
Rows are filtered to the asked disease (or its subtypes) and require a primary
citation (invariant #3).
"""

from __future__ import annotations

from src.connectors.opentargets import _post
from src.connectors.opentargets_genetics import _direction, _effect, _evidence_type
from src.question import NodeType, Question
from src.schema import (
    Assumption,
    Dimension,
    EvidenceItem,
    Readout,
    System,
)

_DATASOURCES = ["eva", "gwas_credible_sets", "gene_burden"]

_QUERY = """
query VariantEvidence($id: String!) {
  variant(variantId: $id) {
    id
    rsIds
    mostSevereConsequence { label }
    evidences(datasourceIds: ["eva", "gwas_credible_sets", "gene_burden"], size: 40) {
      rows {
        datasourceId
        directionOnTarget
        directionOnTrait
        oddsRatio
        oddsRatioConfidenceIntervalLower
        oddsRatioConfidenceIntervalUpper
        beta
        betaConfidenceIntervalLower
        betaConfidenceIntervalUpper
        studyId
        literature
        variantFunctionalConsequence { label }
        disease { id name }
      }
    }
  }
}
"""


def _relevant(row_disease_name: str, target_name: str) -> bool:
    a, b = row_disease_name.lower(), target_name.lower()
    return a in b or b in a


class OpenTargetsVariantConnector:
    connector_id = "opentargets_variant"
    modality = "gwas_finemap"

    def __init__(self, online: bool = False, timeout: float = 25.0, keep: int = 12) -> None:
        self.online = online
        self.timeout = timeout
        self.keep = keep

    def available_for(self, q: Question) -> bool:
        return (
            self.online
            and q.source.type == NodeType.VARIANT
            and bool(q.source.id)
            and q.target.type in (NodeType.DISEASE, NodeType.PHENOTYPE)
        )

    async def fetch(self, q: Question) -> list[EvidenceItem]:
        if not self.available_for(q):
            return []
        data = _post(_QUERY, {"id": q.source.id}, self.timeout)
        if not data:
            return []
        var = data.get("variant") or {}
        rows = (var.get("evidences") or {}).get("rows", []) or []
        rsid = (var.get("rsIds") or [q.source.id])[0]
        consequence = (var.get("mostSevereConsequence") or {}).get("label")
        target_name = q.target.label or q.target.display()

        seen: set[tuple] = set()
        items: list[EvidenceItem] = []
        for row in rows:
            dis = (row.get("disease") or {}).get("name") or ""
            if not _relevant(dis, target_name):
                continue
            lit = row.get("literature") or []
            if not lit:
                continue  # invariant #3
            ds = row["datasourceId"]
            key = (ds, dis)
            if key in seen:
                continue
            seen.add(key)
            direction = _direction(row.get("directionOnTarget"), row.get("directionOnTrait"))
            if direction.value == "null":
                continue
            vfc = (row.get("variantFunctionalConsequence") or {}).get("label") or consequence
            dir_target = row.get("directionOnTarget")
            items.append(
                EvidenceItem(
                    id=f"otv_{ds}_{q.source.id}"[:60],
                    target=q.source.symbol or rsid,
                    disease=target_name,
                    dimension=Dimension.GENETIC,
                    evidence_type=_evidence_type(ds, vfc),
                    direction=direction,
                    effect=_effect(row),
                    system=System.HUMAN,
                    readout=Readout.CLINICAL_OUTCOME,
                    assumptions_required=[] if dir_target else [Assumption.CORRECT_DAG],
                    falsified_by=[f"{rsid} shown not to associate with {target_name}"],
                    source=f"PMID:{lit[0]}",
                    provenance_group=f"otgenetics_var_{ds}_{q.source.id}",
                    notes=(
                        f"Variant-level evidence for {rsid} ({vfc or 'variant'}) via {ds}; "
                        f"reported disease: {dis}; directionOnTrait={row.get('directionOnTrait')}"
                        + (f", directionOnTarget={dir_target}" if dir_target
                           else "; gene-level direction inferred from the disease-risk sign")
                    ),
                )
            )
            if len(items) >= self.keep:
                break
        return items
