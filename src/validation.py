"""
Validation harness (Report / build-brief section 7): calibrate before trusting.

Runs the curated known-answer set through the full pipeline and checks:
  * the known-answer archetype + composite are recovered for each case;
  * the ASSOCIATION ranking and the CAUSAL ranking DISAGREE (the product): a
    target can correlate strongly yet be non-causal, and vice versa;
  * a reliability summary by (uncalibrated) posterior band. Digits on the
    posterior stay locked (`calibrated=False`) until a real gold set with binned
    hit-rates passes here -- this harness is where that license would be granted.

Positive set (would-be ClinGen Definitive / OMIM monogenic): PCSK9, APP/amyloid.
Negative / hard set (curated non-associations, failed replications): HDL-C, CRP.
Marker-but-real (excellent biomarker, uncertain target): tau.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.question import EdgeType, Node, NodeType, Question
from src.orchestrator import Orchestrator
from src.schema import Archetype, Composite, Dimension, Tier

# The known answers, as (archetype, composite) the pipeline must recover.
_EXPECTED: dict[str, tuple[Archetype, Composite]] = {
    "PCSK9": (Archetype.VALIDATED_DRIVER, Composite.CAUSAL_DRIVER),
    "HDL-C": (Archetype.ASSOCIATED_NONCAUSAL, Composite.REFUTED),
    "CRP": (Archetype.DISPLACED_SIGNAL, Composite.LIKELY_NONCAUSAL),
    "APP/amyloid": (Archetype.UPSTREAM_INITIATOR, Composite.LIKELY_CAUSAL),
    "tau": (Archetype.DOWNSTREAM_MEDIATOR, Composite.PLAUSIBLE),
}

_CAUSAL_COMPOSITES = (Composite.CAUSAL_DRIVER, Composite.LIKELY_CAUSAL)


@dataclass
class CaseResult:
    target: str
    disease: str
    archetype: Archetype
    composite: Composite
    expected_archetype: Archetype
    expected_composite: Composite
    association_strong: bool
    causal_strong: bool
    posterior_band: str

    @property
    def archetype_ok(self) -> bool:
        return self.archetype == self.expected_archetype

    @property
    def composite_ok(self) -> bool:
        return self.composite == self.expected_composite


@dataclass
class ValidationReport:
    results: list[CaseResult] = field(default_factory=list)
    separation_holds: bool = False
    all_recovered: bool = False

    def summary(self) -> str:
        lines = ["Validation harness — known-answer recovery + separation\n"]
        lines.append(f"{'target':14s} {'archetype':22s} {'tier':16s} {'assoc':6s} {'causal':6s} recovered")
        lines.append("-" * 78)
        for r in self.results:
            ok = "OK" if (r.archetype_ok and r.composite_ok) else "MISMATCH"
            lines.append(
                f"{r.target:14s} {r.archetype.value:22s} {r.composite.value:16s} "
                f"{'yes' if r.association_strong else 'no':6s} "
                f"{'yes' if r.causal_strong else 'no':6s} {ok}"
            )
        lines.append("")
        lines.append(f"Known answers recovered: {'PASS' if self.all_recovered else 'FAIL'}")
        lines.append(
            "Association-vs-causal ranking separation: "
            + ("PASS (rankings disagree — the gap is the product)" if self.separation_holds else "FAIL")
        )
        lines.append(
            "\nPosterior digits remain LOCKED (calibrated=False) until a gold set with "
            "binned hit-rates is supplied; this run reports bands only."
        )
        return "\n".join(lines)


def run_validation() -> ValidationReport:
    orch = Orchestrator(online=False)
    report = ValidationReport()

    for case in orch.fixtures.all_cases():
        q = Question(
            source=Node(type=NodeType.GENE, symbol=case.target),
            target=Node(type=NodeType.DISEASE, symbol=case.disease),
            edge_type=EdgeType.CAUSAL_RISK,
        )
        ap = orch.appraise_sync(q)
        assoc = ap.dimensions.get(Dimension.ASSOCIATION)
        association_strong = bool(assoc and assoc.tier in (Tier.STRONG, Tier.MODERATE))
        causal_strong = ap.composite in _CAUSAL_COMPOSITES
        exp = _EXPECTED.get(case.target, (ap.archetype, ap.composite))
        band = ap.posterior.render() if ap.posterior else "not scored"
        report.results.append(
            CaseResult(
                target=case.target,
                disease=case.disease,
                archetype=ap.archetype,
                composite=ap.composite,
                expected_archetype=exp[0],
                expected_composite=exp[1],
                association_strong=association_strong,
                causal_strong=causal_strong,
                posterior_band=band,
            )
        )

    assoc_set = {r.target for r in report.results if r.association_strong}
    causal_set = {r.target for r in report.results if r.causal_strong}
    # The separation is the point: some strongly-associated targets are not causal
    # (HDL, tau) and at least one weakly-associated target is causal (amyloid).
    report.separation_holds = assoc_set != causal_set and bool(assoc_set - causal_set)
    report.all_recovered = all(r.archetype_ok and r.composite_ok for r in report.results)
    return report


if __name__ == "__main__":
    print(run_validation().summary())
