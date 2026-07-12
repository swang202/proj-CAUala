"""
FixtureConnector -- the offline, provenance-bearing evidence source.

Serves the curated records in registry/curated_evidence.yaml so that
`variant/gene -> disease` questions run end-to-end with real (hand-curated)
records and no network. This is what makes the pipeline reproducible and testable
offline, and it is the reference backbone the demo runs against.

It also surfaces per-case metadata the scorer needs but cannot derive from a
target's own evidence: the base-rate prior, the disease area (for exemplar
selection), and `upstream_node_carries_signal` (the pathway fact that
distinguishes a displaced signal from a plain marker).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from src.question import Question
from src.schema import EffectSize, EvidenceItem

_CURATED_PATH = Path(__file__).resolve().parent.parent.parent / "registry" / "curated_evidence.yaml"


def _norm(s: str) -> str:
    return s.strip().lower().replace("'", "").replace("-", " ").strip()


@dataclass
class CuratedCase:
    """A parsed case: its EvidenceItems plus the metadata the scorer needs."""

    target: str
    disease: str
    disease_area: Optional[str]
    upstream_node_carries_signal: bool
    prior: float
    prior_source: str
    next_experiment: str
    items: list[EvidenceItem]
    target_aliases: list[str] = field(default_factory=list)
    disease_aliases: list[str] = field(default_factory=list)

    def matches(self, q: Question) -> bool:
        src = _norm(q.source.display())
        tgt = _norm(q.target.display())
        target_hit = any(_norm(a) == src for a in [self.target, *self.target_aliases])
        disease_hit = any(_norm(a) == tgt for a in [self.disease, *self.disease_aliases])
        return target_hit and disease_hit


def _build_item(case_target: str, case_disease: str, raw: dict) -> EvidenceItem:
    effect = None
    if raw.get("effect"):
        effect = EffectSize(**raw["effect"])
    return EvidenceItem(
        id=raw["id"],
        target=case_target,
        disease=case_disease,
        dimension=raw["dimension"],
        evidence_type=raw["evidence_type"],
        direction=raw["direction"],
        effect=effect,
        system=raw["system"],
        readout=raw["readout"],
        assumptions_required=raw.get("assumptions_required", []),
        falsified_by=raw.get("falsified_by", []),
        source=raw["source"],
        provenance_group=raw["provenance_group"],
        contradicts=raw.get("contradicts", []),
        notes=raw.get("notes"),
    )


def _load_cases() -> list[CuratedCase]:
    with open(_CURATED_PATH) as fh:
        doc = yaml.safe_load(fh)
    cases: list[CuratedCase] = []
    for c in doc["cases"]:
        items = [_build_item(c["target"], c["disease"], e) for e in c["evidence"]]
        cases.append(
            CuratedCase(
                target=c["target"],
                disease=c["disease"],
                disease_area=c.get("disease_area"),
                upstream_node_carries_signal=bool(c.get("upstream_node_carries_signal", False)),
                prior=float(c.get("prior", 0.05)),
                prior_source=c.get("prior_source", "unspecified base rate"),
                next_experiment=c.get("next_experiment", "").strip(),
                items=items,
                target_aliases=c.get("target_aliases", []),
                disease_aliases=c.get("disease_aliases", []),
            )
        )
    return cases


class FixtureConnector:
    """Offline backbone. Implements the BaseConnector contract and, additionally,
    exposes the matched case metadata via `case_for`."""

    connector_id = "fixtures"
    modality = "integrated_backbone"

    def __init__(self) -> None:
        self._cases = _load_cases()

    def case_for(self, q: Question) -> Optional[CuratedCase]:
        for case in self._cases:
            if case.matches(q):
                return case
        return None

    def available_for(self, q: Question) -> bool:
        return self.case_for(q) is not None

    async def fetch(self, q: Question) -> list[EvidenceItem]:
        case = self.case_for(q)
        return list(case.items) if case else []

    def all_cases(self) -> list[CuratedCase]:
        return list(self._cases)
