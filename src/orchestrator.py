"""
Orchestrator -- routes a Question through retrieval, scoring and assembly.

Flow:
  1. harmonize the question (resolve ids, flag coarse labels);
  2. match it to an evidence stack in the registry -> ranked modalities;
  3. run the available connectors (offline: the FixtureConnector backbone);
  4. assemble each dimension deterministically (assemble_dimension);
  5. GATE -> composite; classify -> archetype; derive INUS; compute the
     subordinate posterior;
  6. record transparency: not_examined, stopped_because (VOI), conflicts,
     coarse_label_warning, next_experiment.

The LLM never enters here. Everything is a pure function of retrieved records.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import yaml

from src.connectors.base import CACHE
from src.connectors.fixtures import CuratedCase, FixtureConnector
from src.connectors.opentargets import OpenTargetsConnector
from src.harmonization import Harmonization, harmonize
from src.question import Question
from src.schema import (
    Composite,
    Context,
    Dimension,
    DimensionAssessment,
    Direction,
    EvidenceItem,
    TargetAppraisal,
    Tier,
)
from src.scoring import apply_gates, classify_archetype
from src.scoring_engine import (
    assemble_dimension,
    compute_posterior,
    derive_inus,
    voi_should_stop,
)

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "registry" / "evidence_stacks.yaml"

# Which dimension each registry modality feeds. Used to report examined vs
# not_examined modalities against the retrieved evidence.
_MODALITY_DIMENSION: dict[str, Dimension] = {
    "mendelian_randomization": Dimension.GENETIC,
    "mendelian_randomization_reverse": Dimension.GENETIC,
    "mendelian_randomization_drugtarget": Dimension.GENETIC,
    "eqtl_coloc": Dimension.GENETIC,
    "eqtl_transacting": Dimension.GENETIC,
    "gwas_finemap": Dimension.GENETIC,
    "clinvar_omim_curation": Dimension.GENETIC,
    "constraint_gate": Dimension.MECHANISM,
    "integrated_backbone": Dimension.ASSOCIATION,
    "perturb_seq": Dimension.INTERVENTION,
    "crispr_ko_depmap": Dimension.INTERVENTION,
    "l1000_signature": Dimension.INTERVENTION,
    "coexpression": Dimension.ASSOCIATION,
    "longitudinal_omics": Dimension.TEMPORAL,
    "case_control_deg": Dimension.ASSOCIATION,
    "rct": Dimension.INTERVENTION,
}


def load_registry() -> list[dict]:
    with open(_REGISTRY_PATH) as fh:
        return yaml.safe_load(fh)["stacks"]


class Orchestrator:
    def __init__(self, online: bool = False) -> None:
        self.online = online
        self.registry = load_registry()
        self.fixtures = FixtureConnector()
        self.opentargets = OpenTargetsConnector(online=online)

    # -- registry matching --------------------------------------------------

    def match_stack(self, q: Question) -> Optional[dict]:
        key = q.stack_key()
        for entry in self.registry:
            m = entry["match"]
            if (m["source"], m["target"], m["edge"]) == key:
                return entry
        return None

    # -- retrieval ----------------------------------------------------------

    async def _retrieve(self, q: Question) -> tuple[list[EvidenceItem], list[str], Optional[CuratedCase]]:
        """Run available connectors. Returns (items, queried_connector_ids, case)."""
        items: list[EvidenceItem] = []
        queried: list[str] = []

        cached = CACHE.get(CACHE.key(self.fixtures.connector_id, q))
        if cached is not None:
            items.extend(cached)
            queried.append(self.fixtures.connector_id)
        elif self.fixtures.available_for(q):
            fetched = await self.fixtures.fetch(q)
            CACHE.set(CACHE.key(self.fixtures.connector_id, q), fetched)
            items.extend(fetched)
            queried.append(self.fixtures.connector_id)

        if self.online and self.opentargets.available_for(q):
            ot = await self.opentargets.fetch(q)
            items.extend(ot)
            queried.append(self.opentargets.connector_id)

        case = self.fixtures.case_for(q)
        return items, queried, case

    # -- conflict surfacing (invariant #5) ----------------------------------

    @staticmethod
    def _find_conflicts(dimensions: dict[Dimension, DimensionAssessment]) -> list[str]:
        conflicts: list[str] = []
        # Directional disagreement between a supportive causal dimension and a
        # contradicted one is a real conflict -- surface it, never average it.
        contradicted = [d for d, a in dimensions.items() if a.tier == Tier.CONTRADICTED]
        supportive = [
            d
            for d, a in dimensions.items()
            if a.tier in (Tier.STRONG, Tier.MODERATE)
            and d in (Dimension.INTERVENTION, Dimension.GENETIC, Dimension.TEMPORAL, Dimension.MEDIATION)
        ]
        for c in contradicted:
            for s in supportive:
                conflicts.append(
                    f"{s.value} supports the arrow while {c.value} contradicts it; "
                    "surfaced, not averaged."
                )
        # Association direction opposing genetics (marker that points the 'wrong' way).
        assoc = dimensions.get(Dimension.ASSOCIATION)
        gen = dimensions.get(Dimension.GENETIC)
        if assoc and gen and gen.tier == Tier.CONTRADICTED and assoc.items:
            adirs = {i.direction for i in assoc.items if i.direction != Direction.NULL}
            if adirs:
                conflicts.append(
                    "Association is directional but genetics is null/contradicted: "
                    "the correlation is real, its causal reading is not."
                )
        return conflicts

    # -- main entry ---------------------------------------------------------

    async def appraise(self, q: Question) -> TargetAppraisal:
        harm: Harmonization = harmonize(q)
        q = harm.question

        stack_entry = self.match_stack(q)
        stack = stack_entry["canonical_stack"] if stack_entry else []

        items, queried, case = await self._retrieve(q)

        # Group retrieved items by dimension and assemble each.
        by_dim: dict[Dimension, list[EvidenceItem]] = {}
        for it in items:
            by_dim.setdefault(it.dimension, []).append(it)
        dimensions: dict[Dimension, DimensionAssessment] = {
            d: assemble_dimension(d, its) for d, its in by_dim.items()
        }

        # Walk the stack in retrieval-tier order; a modality is "examined" when its
        # dimension yielded evidence. VOI decides whether the rest were skipped.
        ordered = sorted(stack, key=lambda m: m["tier"])
        examined: list[str] = []
        not_examined_mods: list[str] = []
        remaining: list[dict] = []
        for mod in ordered:
            dim = _MODALITY_DIMENSION.get(mod["modality"])
            if dim is not None and dim in dimensions and dimensions[dim].tier != Tier.ABSENT:
                examined.append(mod["modality"])
            else:
                remaining.append(mod)

        composite = apply_gates(dimensions) if dimensions else Composite.UNVALIDATED

        stopped_because: Optional[str] = None
        if remaining:
            stop, reason = voi_should_stop(composite, examined, remaining)
            if stop:
                stopped_because = reason
                not_examined_mods = [m["modality"] for m in remaining]
            else:
                # We would keep querying, but offline there is nothing more to fetch.
                not_examined_mods = [m["modality"] for m in remaining]
                stopped_because = (
                    "No further records available offline for the unqueried modalities; "
                    "they are reported as gaps rather than silently dropped."
                )

        # Map unexamined modalities to the dimensions they would have informed.
        not_examined_dims = sorted(
            {
                _MODALITY_DIMENSION[m]
                for m in not_examined_mods
                if m in _MODALITY_DIMENSION
                and _MODALITY_DIMENSION[m] not in dimensions
            },
            key=lambda d: d.value,
        )

        # Position + rationale. The pathway fact comes from the case, never guessed.
        upstream = case.upstream_node_carries_signal if case else False
        disease_area = case.disease_area if case else None
        archetype, rationale = classify_archetype(
            dimensions,
            upstream_node_carries_signal=upstream,
            disease_area=disease_area,
        )

        inus = derive_inus(dimensions)

        prior = case.prior if case else 0.05
        prior_source = case.prior_source if case else "default null base rate for gene-disease pairs"
        posterior = compute_posterior(dimensions, composite, prior, prior_source)

        conflicts = self._find_conflicts(dimensions)

        next_experiment = (
            case.next_experiment
            if case and case.next_experiment
            else "Strengthen the weakest causal dimension with a genotype-anchored or "
            "reversible perturbation test."
        )

        context = q.context if q.context.is_scoped() else Context()

        appraisal = TargetAppraisal(
            target=q.source.display(),
            disease=q.target.display(),
            context=context,
            dimensions=dimensions,
            composite=composite,
            archetype=archetype,
            inus=inus,
            posterior=posterior,
            archetype_rationale=rationale,
            next_experiment=next_experiment,
            not_examined=not_examined_dims,
            stopped_because=stopped_because,
            conflicts=conflicts,
            coarse_label_warning=harm.coarse_label_warning,
        )

        # Invariant #8, enforced at the boundary: never emit a posterior above the gate.
        assert appraisal.posterior_respects_gate(), "posterior exceeded gated tier"
        return appraisal

    def appraise_sync(self, q: Question) -> TargetAppraisal:
        return asyncio.run(self.appraise(q))
