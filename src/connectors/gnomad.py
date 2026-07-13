"""
gnomAD connector -- gene constraint as a plausibility gate (keyless GraphQL).

Returns LOEUF / pLI constraint for the source gene as a DIRECTION-LESS mechanism
item. Constraint is a plausibility axis only: a LOF-intolerant gene (low LOEUF,
high pLI) is more plausibly disease-relevant, but per invariant #2 this can NEVER
raise the causal score on its own -- it lands in the mechanism dimension, which
the gate ignores when setting the ceiling. Included to show a second real source
and a non-association axis. Network failure -> [] (a named gap).
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

API_URL = "https://gnomad.broadinstitute.org/api"

_CONSTRAINT_QUERY = """
query Constraint($symbol: String!) {
  gene(gene_symbol: $symbol, reference_genome: GRCh38) {
    gene_id
    symbol
    gnomad_constraint { pli oe_lof oe_lof_lower oe_lof_upper }
  }
}
"""


class GnomadConnector:
    connector_id = "gnomad"
    modality = "constraint_gate"

    def __init__(self, online: bool = False, timeout: float = 25.0) -> None:
        self.online = online
        self.timeout = timeout

    def available_for(self, q: Question) -> bool:
        return self.online and q.source.type in (NodeType.GENE, NodeType.PROTEIN)

    async def fetch(self, q: Question) -> list[EvidenceItem]:
        if not self.available_for(q):
            return []
        # Prefer the canonical gene symbol resolved by harmonization (node.label,
        # e.g. "MAPT") over the free-text entry ("tau", "APP/amyloid"), which gnomAD
        # would not recognise.
        symbol = q.source.label or q.source.symbol or q.source.display()
        # gnomAD rate-limits (~10 req/min); retry with small backoff before giving up.
        import asyncio

        import httpx

        data = None
        for i in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        API_URL,
                        json={"query": _CONSTRAINT_QUERY, "variables": {"symbol": symbol}},
                        headers={"content-type": "application/json"},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                break
            except Exception:
                if i == 2:
                    return []
                await asyncio.sleep(0.5 * (i + 1))
        if data is None:
            return []

        gene = (data.get("data") or {}).get("gene") or {}
        constraint = gene.get("gnomad_constraint") or {}
        loeuf = constraint.get("oe_lof_upper")
        pli = constraint.get("pli")
        if loeuf is None and pli is None:
            return []

        constrained = (loeuf is not None and loeuf < 0.35) or (pli is not None and pli > 0.9)
        verdict = "LOF-intolerant (constrained; plausibly dosage-sensitive)" if constrained else \
            "LOF-tolerant (unconstrained; haploinsufficiency less likely)"
        return [
            EvidenceItem(
                id=f"gnomad_{gene.get('gene_id', symbol)}",
                target=symbol,
                disease=q.target.label or q.target.display(),
                dimension=Dimension.MECHANISM,           # plausibility axis only
                evidence_type=EvidenceType.BIOCHEMICAL_PATHWAY,
                direction=Direction.NULL,                # constraint has no direction
                effect=EffectSize(value=round(loeuf, 3) if loeuf is not None else -1.0, units="LOEUF"),
                system=System.HUMAN,
                readout=Readout.MOLECULAR_PROFILE,
                falsified_by=["Updated gnomAD release reclassifies the gene's constraint"],
                source="10.1038/s41586-020-2308-7",  # gnomAD v2 constraint, Karczewski 2020
                provenance_group=f"gnomad_constraint_{symbol}",
                notes=f"gnomAD GRCh38 constraint: LOEUF={loeuf}, pLI={pli}. {verdict}. "
                      "Plausibility only -- cannot raise the causal tier (invariant #2).",
            )
        ]
