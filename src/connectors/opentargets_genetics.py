"""
Open Targets genetic-evidence connector -- the first DIRECTIONAL live source.

The integrated association score (OpenTargetsConnector) is direction-less. This
connector pulls the underlying genetic evidence for a gene -> disease pair and maps
each record into a directional GENETIC EvidenceItem, from three PD-relevant (and
disease-agnostic) Open Targets datasources:

  * gwas_credible_sets -- fine-mapped common-variant GWAS (a PD GWAS signal);
  * gene_burden        -- rare-variant burden from sequencing studies (seq in cases);
  * eva (ClinVar)      -- curated pathogenic variants (e.g. LRRK2 G2019S in PD).

Direction comes from Open Targets' `directionOnTarget` / `directionOnTrait`
annotations where present; otherwise it is inferred from the disease-risk sign and
flagged with an assumption (gene-level direction needs eQTL colocalization). Every
item is cited to a primary study PMID -- records with no citation are dropped
(invariant #3), never scored.
"""

from __future__ import annotations

from typing import Optional

from src.connectors.opentargets import _post
from src.question import NodeType, Question
from src.schema import (
    Assumption,
    Dimension,
    Direction,
    EffectSize,
    EvidenceItem,
    EvidenceType,
    Readout,
    System,
)

_DATASOURCES = ["gwas_credible_sets", "gene_burden", "eva"]
_DS_LABEL = {
    "gwas_credible_sets": "GWAS credible set (fine-mapped common variant)",
    "gene_burden": "rare-variant burden (sequencing in cases)",
    "eva": "ClinVar curated variant",
}

_QUERY = """
query Genetics($efo: String!, $ens: [String!]!, $ds: [String!]!, $n: Int!) {
  disease(efoId: $efo) {
    name
    evidences(ensemblIds: $ens, datasourceIds: $ds, size: $n) {
      count
      rows {
        datasourceId
        variantRsId
        oddsRatio
        oddsRatioConfidenceIntervalLower
        oddsRatioConfidenceIntervalUpper
        beta
        betaConfidenceIntervalLower
        betaConfidenceIntervalUpper
        directionOnTarget
        directionOnTrait
        studyId
        literature
        variantFunctionalConsequence { label }
      }
    }
  }
}
"""


def _evidence_type(datasource: str, vfc: Optional[str]) -> EvidenceType:
    if datasource == "gwas_credible_sets":
        return EvidenceType.GWAS_COLOCALIZATION
    if datasource == "gene_burden":
        return EvidenceType.RARE_PENETRANT_VARIANT
    # ClinVar (eva): a coding pathogenic variant is a rare penetrant variant.
    if vfc and any(k in vfc.lower() for k in ("missense", "frameshift", "stop", "splice", "start_lost")):
        return EvidenceType.RARE_PENETRANT_VARIANT
    return EvidenceType.GWAS_NEAREST_GENE


def _direction(dir_target: Optional[str], dir_trait: Optional[str]) -> Direction:
    g = (dir_target or "").lower()
    t = (dir_trait or "").lower()
    up = any(k in g for k in ("increas", "gof", "gain"))
    down = any(k in g for k in ("decreas", "lof", "loss"))
    if t == "risk":
        return Direction.DOWN_HARMS if down else Direction.UP_HARMS
    if t == "protective":
        return Direction.UP_PROTECTS if up else Direction.DOWN_PROTECTS
    return Direction.NULL


def _effect(row: dict) -> Optional[EffectSize]:
    orr = row.get("oddsRatio")
    if orr is not None:
        return EffectSize(
            value=round(float(orr), 3),
            ci_low=row.get("oddsRatioConfidenceIntervalLower"),
            ci_high=row.get("oddsRatioConfidenceIntervalUpper"),
            units="OR",
        )
    beta = row.get("beta")
    if beta is not None:
        return EffectSize(
            value=round(float(beta), 3),
            ci_low=row.get("betaConfidenceIntervalLower"),
            ci_high=row.get("betaConfidenceIntervalUpper"),
            units="beta (log-odds)",
        )
    return None


class OpenTargetsGeneticsConnector:
    connector_id = "opentargets_genetics"
    modality = "gwas_finemap"

    def __init__(self, online: bool = False, timeout: float = 25.0, max_rows: int = 50, keep: int = 12) -> None:
        self.online = online
        self.timeout = timeout
        self.max_rows = max_rows
        self.keep = keep

    def available_for(self, q: Question) -> bool:
        return (
            self.online
            and q.source.type in (NodeType.GENE, NodeType.PROTEIN, NodeType.VARIANT)
            and q.target.type in (NodeType.DISEASE, NodeType.PHENOTYPE)
            and (q.source.id or "").startswith("ENSG")
            and q.target.id is not None
        )

    async def fetch(self, q: Question) -> list[EvidenceItem]:
        if not self.available_for(q):
            return []
        data = _post(
            _QUERY,
            {"efo": q.target.id, "ens": [q.source.id], "ds": _DATASOURCES, "n": self.max_rows},
            self.timeout,
        )
        if not data:
            return []
        rows = (data.get("disease") or {}).get("evidences", {}).get("rows", []) or []

        gene = q.source.label or q.source.symbol or q.source.id or "target"
        disease = q.target.label or q.target.display()
        seen: set[tuple[str, str]] = set()
        items: list[EvidenceItem] = []
        for row in rows:
            lit = row.get("literature") or []
            if not lit:
                continue  # invariant #3: no citation -> not scored
            ds = row["datasourceId"]
            rs = row.get("variantRsId") or row.get("studyId") or ""
            key = (ds, rs)
            if key in seen:
                continue
            seen.add(key)
            direction = _direction(row.get("directionOnTarget"), row.get("directionOnTrait"))
            if direction == Direction.NULL:
                continue  # no usable direction -> skip rather than pad with a null
            vfc = (row.get("variantFunctionalConsequence") or {}).get("label")
            dir_target = row.get("directionOnTarget")
            note = (
                f"Open Targets genetic evidence via {_DS_LABEL.get(ds, ds)}"
                + (f"; variant {rs}" if rs else "")
                + (f"; {vfc}" if vfc else "")
                + f"; directionOnTrait={row.get('directionOnTrait')}"
                + (
                    f", directionOnTarget={dir_target}"
                    if dir_target
                    else "; gene-level direction inferred from the disease-risk sign (eQTL colocalization would confirm)"
                )
            )
            items.append(
                EvidenceItem(
                    id=f"otg_{ds}_{rs}"[:60],
                    target=gene,
                    disease=disease,
                    dimension=Dimension.GENETIC,
                    evidence_type=_evidence_type(ds, vfc),
                    direction=direction,
                    effect=_effect(row),
                    system=System.HUMAN,
                    readout=Readout.CLINICAL_OUTCOME,
                    assumptions_required=[] if dir_target else [Assumption.CORRECT_DAG],
                    falsified_by=[f"{rs or 'the variant'} shown not to associate with {disease}"],
                    source=f"PMID:{lit[0]}",
                    provenance_group=f"otgenetics_{ds}_{rs}",
                    notes=note,
                )
            )
            if len(items) >= self.keep:
                break
        return items
