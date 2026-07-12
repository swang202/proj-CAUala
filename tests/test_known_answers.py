"""
Validation on known answers. THIS IS THE SPEC.

These cases are ones where the field has already paid for the answer. The
audience knows them. Watching the tool recover them is the entire demonstration.

Written BEFORE the scoring engine. If classify(HDL) != HDL_pattern, the engine
is wrong -- not the test.

CURATION WARNING
----------------
The effect sizes, PMIDs, and DOIs below are PLACEHOLDERS marked with `TODO:cite`.
They must be replaced by hand, from papers actually read, before this leaves the
repo. A hallucinated citation in the demo would undercut the entire
assumption-forward, evidence-inspectable thesis of the tool.

The *structure* of each case -- which dimensions are strong, which are null,
which direction the evidence points -- is the part that encodes the known answer,
and that part is correct as written.
"""

import pytest

from src.schema import (
    Archetype,
    Assumption,
    Composite,
    Dimension,
    DimensionAssessment,
    Direction,
    EffectSize,
    EvidenceItem,
    EvidenceType,
    Readout,
    System,
    Tier,
)
from src.scoring import apply_gates, classify_archetype


# ---------------------------------------------------------------------------
# Case 1: PCSK9 / cardiovascular disease -- THE DRIVER
#
# Loss-of-function alleles are protective. Gain-of-function causes familial
# hypercholesterolemia. MR is clean. RCTs (evolocumab, alirocumab) succeeded.
# Bidirectional, multi-modal, converging. This should score maximum.
# ---------------------------------------------------------------------------


@pytest.fixture
def pcsk9_evidence() -> dict[Dimension, DimensionAssessment]:
    genetic_items = [
        EvidenceItem(
            id="pcsk9_lof",
            target="PCSK9",
            disease="coronary artery disease",
            dimension=Dimension.GENETIC,
            evidence_type=EvidenceType.PROTECTIVE_ALLELE,
            direction=Direction.DOWN_PROTECTS,
            effect=EffectSize(value=0.12, ci_low=0.03, ci_high=0.45, units="OR"),
            system=System.HUMAN,
            readout=Readout.CLINICAL_OUTCOME,
            assumptions_required=[Assumption.NO_HORIZONTAL_PLEIOTROPY],
            falsified_by=["LOF carriers show no reduction in CHD incidence"],
            source="PMID:16554528",  # TODO:cite -- verify Cohen et al. NEJM 2006
            provenance_group="pcsk9_lof_aric",
        ),
        EvidenceItem(
            id="pcsk9_gof",
            target="PCSK9",
            disease="coronary artery disease",
            dimension=Dimension.GENETIC,
            evidence_type=EvidenceType.RARE_PENETRANT_VARIANT,
            direction=Direction.UP_HARMS,
            effect=EffectSize(value=2.8, ci_low=1.9, ci_high=4.1, units="OR"),
            system=System.HUMAN,
            readout=Readout.CLINICAL_OUTCOME,
            assumptions_required=[],
            falsified_by=["GOF carriers show normal LDL and normal CHD risk"],
            source="10.1038/ng1161",  # TODO:cite -- verify Abifadel et al. 2003
            provenance_group="pcsk9_gof_fh",
        ),
    ]

    intervention_items = [
        EvidenceItem(
            id="pcsk9_rct",
            target="PCSK9",
            disease="coronary artery disease",
            dimension=Dimension.INTERVENTION,
            evidence_type=EvidenceType.HUMAN_RCT,
            direction=Direction.DOWN_PROTECTS,
            effect=EffectSize(value=0.85, ci_low=0.79, ci_high=0.92, units="HR"),
            system=System.HUMAN,
            readout=Readout.CLINICAL_OUTCOME,
            assumptions_required=[],  # randomization does the work
            falsified_by=["No reduction in MACE despite LDL lowering"],
            source="PMID:28304224",  # TODO:cite -- verify FOURIER
            provenance_group="pcsk9_fourier",
        ),
    ]

    return {
        Dimension.GENETIC: DimensionAssessment(
            dimension=Dimension.GENETIC,
            tier=Tier.STRONG,
            items=genetic_items,
            falsifiability="Would drop if MR with valid instruments showed null.",
        ),
        Dimension.INTERVENTION: DimensionAssessment(
            dimension=Dimension.INTERVENTION,
            tier=Tier.STRONG,
            items=intervention_items,
            falsifiability="Would drop if outcome trials showed no MACE reduction.",
        ),
        Dimension.ASSOCIATION: DimensionAssessment(
            dimension=Dimension.ASSOCIATION, tier=Tier.MODERATE, items=[]
        ),
        Dimension.MECHANISM: DimensionAssessment(
            dimension=Dimension.MECHANISM, tier=Tier.STRONG, items=[]
        ),
    }


def test_pcsk9_is_causal_driver(pcsk9_evidence):
    assert apply_gates(pcsk9_evidence) == Composite.CAUSAL_DRIVER


def test_pcsk9_archetype(pcsk9_evidence):
    archetype, _ = classify_archetype(pcsk9_evidence)
    assert archetype == Archetype.VALIDATED_DRIVER


def test_pcsk9_bidirectional(pcsk9_evidence):
    """LOF protects, GOF harms. Bidirectional control of the same axis."""
    assert pcsk9_evidence[Dimension.GENETIC].has_bidirectional_support


# ---------------------------------------------------------------------------
# Case 2: HDL (via CETP) / cardiovascular disease -- THE MARKER
#
# Decades of clean epidemiology. Null MR on HDL-raising variants. Failed CETP
# inhibitor trials (torcetrapib, dalcetrapib, evacetrapib). The expensive lesson.
# ---------------------------------------------------------------------------


@pytest.fixture
def hdl_evidence() -> dict[Dimension, DimensionAssessment]:
    return {
        Dimension.ASSOCIATION: DimensionAssessment(
            dimension=Dimension.ASSOCIATION,
            tier=Tier.STRONG,
            items=[
                EvidenceItem(
                    id="hdl_epi",
                    target="HDL-C",
                    disease="coronary artery disease",
                    dimension=Dimension.ASSOCIATION,
                    evidence_type=EvidenceType.OBSERVATIONAL_COHORT,
                    direction=Direction.UP_PROTECTS,
                    effect=EffectSize(value=0.78, ci_low=0.74, ci_high=0.82, units="HR per SD"),
                    system=System.HUMAN,
                    readout=Readout.CLINICAL_OUTCOME,
                    assumptions_required=[Assumption.NO_UNMEASURED_CONFOUNDING],
                    falsified_by=["Association attenuates fully on adjustment"],
                    source="PMID:2642759",  # TODO:cite -- verify Framingham
                    provenance_group="hdl_framingham",
                )
            ],
            falsifiability="Robust. Association is real; causal interpretation is not.",
        ),
        Dimension.GENETIC: DimensionAssessment(
            dimension=Dimension.GENETIC,
            tier=Tier.CONTRADICTED,
            items=[
                EvidenceItem(
                    id="hdl_mr_null",
                    target="HDL-C",
                    disease="coronary artery disease",
                    dimension=Dimension.GENETIC,
                    evidence_type=EvidenceType.MENDELIAN_RANDOMIZATION,
                    direction=Direction.NULL,
                    effect=EffectSize(value=0.98, ci_low=0.91, ci_high=1.06, units="OR per SD"),
                    system=System.HUMAN,
                    readout=Readout.CLINICAL_OUTCOME,
                    assumptions_required=[
                        Assumption.NO_HORIZONTAL_PLEIOTROPY,
                        Assumption.INSTRUMENT_RELEVANCE,
                    ],
                    falsified_by=["MR with better instruments shows protective effect"],
                    source="10.1016/S0140-6736(12)60312-2",  # TODO:cite -- verify Voight 2012
                    provenance_group="hdl_mr_voight",
                )
            ],
            falsifiability="Would reverse if pleiotropy-robust MR showed protection.",
        ),
        Dimension.INTERVENTION: DimensionAssessment(
            dimension=Dimension.INTERVENTION,
            tier=Tier.CONTRADICTED,
            items=[
                EvidenceItem(
                    id="cetp_fail",
                    target="HDL-C",
                    disease="coronary artery disease",
                    dimension=Dimension.INTERVENTION,
                    evidence_type=EvidenceType.HUMAN_RCT,
                    direction=Direction.NULL,
                    effect=EffectSize(value=1.02, ci_low=0.93, ci_high=1.12, units="HR"),
                    system=System.HUMAN,
                    readout=Readout.CLINICAL_OUTCOME,
                    assumptions_required=[],
                    falsified_by=["A CETP inhibitor reduces MACE via HDL raising"],
                    source="PMID:17984165",  # TODO:cite -- verify ILLUMINATE
                    provenance_group="cetp_illuminate",
                    notes=(
                        "Raised HDL substantially. No benefit. torcetrapib had "
                        "off-target BP effects; dalcetrapib and evacetrapib were "
                        "cleaner and still null."
                    ),
                )
            ],
            falsifiability="Dispositive. Intervention was performed and failed.",
        ),
        Dimension.MECHANISM: DimensionAssessment(
            dimension=Dimension.MECHANISM,
            tier=Tier.STRONG,
            items=[],
            falsifiability=(
                "Reverse cholesterol transport is a beautiful story. It is also the "
                "dimension that made HDL look great. Mechanism is the weakest "
                "causal dimension."
            ),
        ),
    }


def test_hdl_is_refuted(hdl_evidence):
    """Contradicted intervention evidence is close to dispositive."""
    assert apply_gates(hdl_evidence) == Composite.REFUTED


def test_hdl_archetype(hdl_evidence):
    archetype, rationale = classify_archetype(hdl_evidence)
    assert archetype == Archetype.ASSOCIATED_NONCAUSAL
    assert "marker, not target" in rationale.lower()


def test_strong_mechanism_cannot_rescue_hdl(hdl_evidence):
    """
    The core anti-CETP rule: mechanism at 10/10 does not lift the composite.
    If this test fails, someone has reintroduced a weighted sum.
    """
    assert hdl_evidence[Dimension.MECHANISM].tier == Tier.STRONG
    assert apply_gates(hdl_evidence) in (Composite.REFUTED, Composite.LIKELY_NONCAUSAL)


# ---------------------------------------------------------------------------
# Case 3: CRP / cardiovascular disease -- THE WRONG NODE
#
# CRP correlates strongly. MR on CRP variants: null. But IL-6 signalling IS
# causal (IL6R variants; CANTOS/canakinumab). The causal signal sits one node
# upstream. This cannot be seen from CRP's own evidence -- it requires pathway
# context, which is why `upstream_node_carries_signal` is passed explicitly.
# ---------------------------------------------------------------------------


@pytest.fixture
def crp_evidence() -> dict[Dimension, DimensionAssessment]:
    return {
        Dimension.ASSOCIATION: DimensionAssessment(
            dimension=Dimension.ASSOCIATION,
            tier=Tier.STRONG,
            items=[],
            falsifiability="Association is robust and replicated.",
        ),
        Dimension.GENETIC: DimensionAssessment(
            dimension=Dimension.GENETIC,
            tier=Tier.CONTRADICTED,
            items=[
                EvidenceItem(
                    id="crp_mr_null",
                    target="CRP",
                    disease="coronary artery disease",
                    dimension=Dimension.GENETIC,
                    evidence_type=EvidenceType.MENDELIAN_RANDOMIZATION,
                    direction=Direction.NULL,
                    effect=EffectSize(value=1.00, ci_low=0.90, ci_high=1.13, units="OR per SD"),
                    system=System.HUMAN,
                    readout=Readout.CLINICAL_OUTCOME,
                    assumptions_required=[Assumption.NO_HORIZONTAL_PLEIOTROPY],
                    falsified_by=["CRP-raising variants increase CHD risk"],
                    source="10.1136/bmj.d548",  # TODO:cite -- verify CRP CHD Genetics Collab
                    provenance_group="crp_mr_collab",
                    notes="IL6R variants, by contrast, ARE associated with CHD risk.",
                )
            ],
            falsifiability="Would reverse if CRP-specific instruments showed effect.",
        ),
        Dimension.MECHANISM: DimensionAssessment(
            dimension=Dimension.MECHANISM, tier=Tier.MODERATE, items=[]
        ),
    }


def test_crp_is_wrong_node(crp_evidence):
    """Requires pathway context: IL6R carries the signal that CRP does not."""
    archetype, rationale = classify_archetype(
        crp_evidence, upstream_node_carries_signal=True
    )
    assert archetype == Archetype.DISPLACED_SIGNAL
    assert "upstream" in rationale.lower()


def test_displaced_signal_undetectable_without_pathway_context(crp_evidence):
    """
    Honest limitation: absent pathway context, a displaced-signal target is
    indistinguishable from a plain marker. The diagnosis is not derivable from
    the target's own evidence -- it requires knowing that a neighbouring node
    carries the causal signal. This test documents that.
    """
    archetype, _ = classify_archetype(crp_evidence, upstream_node_carries_signal=False)
    assert archetype == Archetype.ASSOCIATED_NONCAUSAL


# ---------------------------------------------------------------------------
# Case 4: APP / amyloid in Alzheimer's -- THE CONTESTED INITIATOR
#
# Strong genetics: APP/PSEN1/PSEN2 mutations cause autosomal-dominant AD;
# APP duplication (trisomy 21) causes early AD by dosage alone; the A673T
# Icelandic allele is PROTECTIVE. Bidirectional at the gene level.
#
# Yet plaque burden correlates poorly with cognition. DIAN shows amyloid
# changing decades before cognition, then plateauing. Anti-amyloid antibodies
# give real but modest benefit.
#
# This is exactly what an upstream initiator predicts. Correlation decays with
# causal distance.
# ---------------------------------------------------------------------------


@pytest.fixture
def amyloid_evidence() -> dict[Dimension, DimensionAssessment]:
    return {
        Dimension.GENETIC: DimensionAssessment(
            dimension=Dimension.GENETIC,
            tier=Tier.STRONG,
            items=[
                EvidenceItem(
                    id="app_dominant",
                    target="APP/amyloid",
                    disease="Alzheimer's disease",
                    dimension=Dimension.GENETIC,
                    evidence_type=EvidenceType.RARE_PENETRANT_VARIANT,
                    direction=Direction.UP_HARMS,
                    system=System.HUMAN,
                    readout=Readout.CLINICAL_OUTCOME,
                    assumptions_required=[],
                    falsified_by=["APP mutation carriers do not develop AD"],
                    source="10.1038/349704a0",  # TODO:cite -- verify Goate et al. 1991
                    provenance_group="app_adad",
                ),
                EvidenceItem(
                    id="app_a673t",
                    target="APP/amyloid",
                    disease="Alzheimer's disease",
                    dimension=Dimension.GENETIC,
                    evidence_type=EvidenceType.PROTECTIVE_ALLELE,
                    direction=Direction.DOWN_PROTECTS,
                    system=System.HUMAN,
                    readout=Readout.CLINICAL_OUTCOME,
                    assumptions_required=[],
                    falsified_by=["A673T carriers show normal AD incidence"],
                    source="10.1038/nature11283",  # TODO:cite -- verify Jonsson et al. 2012
                    provenance_group="app_iceland",
                    notes=(
                        "Same gene, opposite direction. Reduces Abeta production and "
                        "lowers AD risk. The causal unit is not the gene -- it is a "
                        "specific perturbation of one processing pathway."
                    ),
                ),
            ],
            falsifiability="Would drop if ADAD pedigrees failed to co-segregate.",
        ),
        Dimension.ASSOCIATION: DimensionAssessment(
            dimension=Dimension.ASSOCIATION,
            tier=Tier.WEAK,
            items=[],
            falsifiability=(
                "Plaque burden correlates poorly with cognitive status; many "
                "cognitively normal elderly carry heavy plaque load at autopsy. "
                "NOTE: this may be a measurement-validity problem (soluble oligomers "
                "vs. deposited fibrils), not a causal-position problem."
            ),
        ),
        Dimension.TEMPORAL: DimensionAssessment(
            dimension=Dimension.TEMPORAL,
            tier=Tier.STRONG,
            items=[
                EvidenceItem(
                    id="dian_cascade",
                    target="APP/amyloid",
                    disease="Alzheimer's disease",
                    dimension=Dimension.TEMPORAL,
                    evidence_type=EvidenceType.ANCHORED_ONSET_COHORT,
                    direction=Direction.UP_HARMS,
                    system=System.HUMAN,
                    readout=Readout.BIOMARKER,
                    assumptions_required=[Assumption.NO_SELECTION_BIAS],
                    falsified_by=["Amyloid change follows rather than precedes tau"],
                    source="10.1056/NEJMoa1202753",  # TODO:cite -- verify Bateman 2012 DIAN
                    provenance_group="dian_bateman",
                    notes=(
                        "Mutation carriers have predictable onset, giving a natural "
                        "time axis anchored to a known genetic driver. Amyloid changes "
                        "decades before tau, before neurodegeneration, before cognition."
                    ),
                )
            ],
            falsifiability="Would drop if the biomarker ordering reversed.",
        ),
        Dimension.INTERVENTION: DimensionAssessment(
            dimension=Dimension.INTERVENTION,
            tier=Tier.MODERATE,
            items=[
                EvidenceItem(
                    id="lecanemab",
                    target="APP/amyloid",
                    disease="Alzheimer's disease",
                    dimension=Dimension.INTERVENTION,
                    evidence_type=EvidenceType.HUMAN_RCT,
                    direction=Direction.DOWN_PROTECTS,
                    system=System.HUMAN,
                    readout=Readout.CLINICAL_OUTCOME,
                    assumptions_required=[],
                    falsified_by=["Amyloid clearance yields zero clinical benefit"],
                    source="10.1056/NEJMoa2212948",  # TODO:cite -- verify CLARITY-AD
                    provenance_group="lecanemab_clarity",
                    notes=(
                        "Real but MODEST benefit. Exactly what an upstream, early-acting "
                        "initiator predicts when intervened on late. Contested: some read "
                        "the effect as clinically marginal or confounded by ARIA-related "
                        "unblinding."
                    ),
                )
            ],
            falsifiability="Would drop if larger trials showed null.",
        ),
        Dimension.MECHANISM: DimensionAssessment(
            dimension=Dimension.MECHANISM, tier=Tier.STRONG, items=[]
        ),
    }


def test_amyloid_is_upstream_initiator(amyloid_evidence):
    archetype, rationale = classify_archetype(amyloid_evidence)
    assert archetype == Archetype.UPSTREAM_INITIATOR
    assert "early" in rationale.lower()


def test_amyloid_weak_association_does_not_sink_it(amyloid_evidence):
    """
    The thesis, as a test. Weak correlation with disease severity does NOT imply
    weak causal status. Correlation decays with causal distance.
    """
    assert amyloid_evidence[Dimension.ASSOCIATION].tier == Tier.WEAK
    assert apply_gates(amyloid_evidence) in (
        Composite.LIKELY_CAUSAL,
        Composite.CAUSAL_DRIVER,
    )


def test_amyloid_genetic_bidirectionality(amyloid_evidence):
    """A673T protects; ADAD mutations harm. Same gene, opposite directions."""
    assert amyloid_evidence[Dimension.GENETIC].has_bidirectional_support


# ---------------------------------------------------------------------------
# Case 5: Tau / Alzheimer's -- THE DOWNSTREAM MEDIATOR
#
# Tracks cognitive decline far better than amyloid. Braak staging of tangle
# spread follows clinical progression. But: correlating better with outcome is
# what a DOWNSTREAM node does. Proximity to the effector end of the chain, not
# causal primacy.
#
# MAPT mutations cause FTD, not AD -- so tau's independent genetic support for
# AD specifically is weak. Same protein, different disease. Pleiotropy.
# ---------------------------------------------------------------------------


@pytest.fixture
def tau_evidence() -> dict[Dimension, DimensionAssessment]:
    return {
        Dimension.ASSOCIATION: DimensionAssessment(
            dimension=Dimension.ASSOCIATION,
            tier=Tier.STRONG,
            items=[],
            falsifiability=(
                "Tangle burden and anatomical spread track cognitive decline. "
                "Robust. But strong correlation is what a proximate node produces."
            ),
        ),
        Dimension.MEDIATION: DimensionAssessment(
            dimension=Dimension.MEDIATION,
            tier=Tier.MODERATE,
            items=[],
            assumptions_load_bearing=[Assumption.NO_MEDIATOR_OUTCOME_CONFOUNDING],
            falsifiability=(
                "Would drop if the amyloid->cognition effect did not flow through tau. "
                "Requires no unmeasured mediator-outcome confounding, which is almost "
                "certainly violated."
            ),
        ),
        Dimension.GENETIC: DimensionAssessment(
            dimension=Dimension.GENETIC,
            tier=Tier.WEAK,
            items=[],
            falsifiability=(
                "MAPT mutations cause FTD, not AD. Independent genetic support for "
                "tau as an AD driver is weak. Same protein, different disease -- the "
                "causal unit is a perturbation-in-context, not a gene."
            ),
        ),
        Dimension.TEMPORAL: DimensionAssessment(
            dimension=Dimension.TEMPORAL, tier=Tier.MODERATE, items=[]
        ),
        Dimension.MECHANISM: DimensionAssessment(
            dimension=Dimension.MECHANISM, tier=Tier.STRONG, items=[]
        ),
    }


def test_tau_is_downstream_mediator(tau_evidence):
    archetype, rationale = classify_archetype(tau_evidence)
    assert archetype == Archetype.DOWNSTREAM_MEDIATOR
    assert "biomarker" in rationale.lower()


def test_tau_rationale_admits_mediators_are_causal(tau_evidence):
    """
    Guard against the framework's own worst error. A mediator IS causal. The
    ambiguity is about position in the graph -- a relation, not a coordinate --
    and a dimension vector cannot fully resolve it.
    """
    _, rationale = classify_archetype(tau_evidence)
    assert "mediator IS causal" in rationale or "mediator is causal" in rationale.lower()


# ---------------------------------------------------------------------------
# The thesis, stated as a cross-case test
# ---------------------------------------------------------------------------


def test_association_ranking_diverges_from_causal_ranking(
    amyloid_evidence, tau_evidence, hdl_evidence, pcsk9_evidence
):
    """
    THE POINT OF THE TOOL.

    Rank by association: tau and HDL beat amyloid.
    Rank by causal status: amyloid and PCSK9 beat tau and HDL.

    The gap between those two rankings is the quantity of interest.
    """
    assoc_strong = {
        name
        for name, ev in [
            ("amyloid", amyloid_evidence),
            ("tau", tau_evidence),
            ("hdl", hdl_evidence),
            ("pcsk9", pcsk9_evidence),
        ]
        if ev[Dimension.ASSOCIATION].tier == Tier.STRONG
    }

    causal_strong = {
        name
        for name, ev in [
            ("amyloid", amyloid_evidence),
            ("tau", tau_evidence),
            ("hdl", hdl_evidence),
            ("pcsk9", pcsk9_evidence),
        ]
        if apply_gates(ev)
        in (Composite.CAUSAL_DRIVER, Composite.LIKELY_CAUSAL)
    }

    # tau and HDL correlate strongly. Neither is a validated driver.
    assert "tau" in assoc_strong and "hdl" in assoc_strong
    assert "tau" not in causal_strong and "hdl" not in causal_strong

    # amyloid correlates weakly. It is nonetheless causal.
    assert "amyloid" not in assoc_strong
    assert "amyloid" in causal_strong

    # The rankings disagree. That disagreement is the product.
    assert assoc_strong != causal_strong


# ---------------------------------------------------------------------------
# Generalizability guards
#
# The exemplars above are CVD and neurodegeneration because those are the cases
# where the field has already paid for the answer. The TOOL is not a CVD or
# neurodegeneration tool. These tests enforce that.
# ---------------------------------------------------------------------------


def test_classification_is_invariant_to_disease_area(hdl_evidence):
    """
    disease_area picks an illustration. It must never change the verdict.
    An oncologist and a cardiologist with identical evidence get identical
    archetypes.
    """
    areas = [None, "oncology", "cardiovascular", "immunology", "nephrology", "xyzzy"]
    verdicts = {classify_archetype(hdl_evidence, disease_area=a)[0] for a in areas}
    assert len(verdicts) == 1


def test_rationale_is_complete_without_exemplar(hdl_evidence, amyloid_evidence):
    """
    THE SEPARATION INVARIANT.

    The structural rationale must stand alone. If stripping the exemplar clause
    leaves an unintelligible sentence, the rationale has leaked disease content
    into logic that is supposed to be disease-agnostic.
    """
    for ev in (hdl_evidence, amyloid_evidence):
        _, rationale = classify_archetype(ev)
        structural = rationale.split("For illustration")[0].strip()
        assert len(structural) > 80
        assert structural.endswith(".")
        for token in ("HDL", "PCSK9", "amyloid", "tau", "CRP", "Alzheimer"):
            assert token not in structural


def test_archetype_values_are_structural_not_exemplar_named():
    """
    A cancer researcher must never be told their target has 'the tau pattern'.
    Enum VALUES are what surface in APIs, logs, and reports.
    """
    forbidden = ("hdl", "pcsk9", "amyloid", "tau", "crp", "il6")
    for member in Archetype:
        assert not any(f in member.value.lower() for f in forbidden), member.value


def test_oncology_case_classifies_without_any_neuro_or_cvd_context():
    """
    A synthetic oncology target with the associated-noncausal shape. No CVD or
    neuro evidence anywhere. Should classify on structure alone.
    """
    onc = {
        Dimension.ASSOCIATION: DimensionAssessment(
            dimension=Dimension.ASSOCIATION, tier=Tier.STRONG, items=[]
        ),
        Dimension.GENETIC: DimensionAssessment(
            dimension=Dimension.GENETIC, tier=Tier.CONTRADICTED, items=[]
        ),
        Dimension.INTERVENTION: DimensionAssessment(
            dimension=Dimension.INTERVENTION, tier=Tier.ABSENT, items=[]
        ),
        Dimension.MECHANISM: DimensionAssessment(
            dimension=Dimension.MECHANISM, tier=Tier.STRONG, items=[]
        ),
    }
    archetype, rationale = classify_archetype(onc, disease_area="oncology")
    assert archetype == Archetype.ASSOCIATED_NONCAUSAL
    # Exemplar should be drawn from oncology, not defaulted to HDL.
    assert "lung cancer" in rationale or "beta-carotene" in rationale


def test_every_archetype_has_a_structural_rationale():
    """No archetype may depend on an exemplar existing. UNTESTED has none."""
    from src.exemplars import exemplar_for

    assert exemplar_for(Archetype.UNTESTED) is None
    untested = {
        Dimension.MECHANISM: DimensionAssessment(
            dimension=Dimension.MECHANISM, tier=Tier.STRONG, items=[]
        ),
    }
    archetype, rationale = classify_archetype(untested)
    assert archetype == Archetype.UNTESTED
    assert "For illustration" not in rationale
    assert len(rationale) > 80


# ---------------------------------------------------------------------------
# Verdict-tuple invariants (schema extension)
#
# The reconciled DESIGN makes the verdict a (position, necessity/sufficiency,
# context) tuple with a subordinate, gated posterior. These lock that.
# ---------------------------------------------------------------------------

from src.schema import (
    Composite as _Composite,
    Context,
    InusVerdict,
    NSAxis,
    NecessitySufficiency,
    Posterior,
    TargetAppraisal,
)


def test_inus_boxes_from_axes():
    """The two middle boxes are the whole point -- they must be distinguishable."""
    assert InusVerdict(necessity=NSAxis.SUPPORTED, sufficiency=NSAxis.REFUTED).box \
        == NecessitySufficiency.NECESSARY_NOT_SUFFICIENT
    assert InusVerdict(necessity=NSAxis.REFUTED, sufficiency=NSAxis.SUPPORTED).box \
        == NecessitySufficiency.SUFFICIENT_NOT_NECESSARY
    # untested on either arm -> undetermined, never silently a real box
    assert InusVerdict(necessity=NSAxis.SUPPORTED).box \
        == NecessitySufficiency.UNDETERMINED


def test_necessary_not_sufficient_gives_gatekeeper_note():
    v = InusVerdict(necessity=NSAxis.SUPPORTED, sufficiency=NSAxis.REFUTED)
    assert "combination or upstream" in v.therapeutic_note


def test_uncalibrated_posterior_never_shows_bare_float():
    """DESIGN rule: digits only after calibration. Pre-calibration = band + provenance."""
    p = Posterior(value=0.86, prior=0.05, prior_source="curated set", calibrated=False)
    rendered = p.render()
    assert "0.86" not in rendered
    assert "uncalibrated" in rendered
    assert "likely causal" in rendered


def test_calibrated_posterior_shows_digits_with_provenance():
    p = Posterior(
        value=0.86, prior=0.05, prior_source="curated set",
        calibrated=True, reliability_bin="0.9 bin, hit-rate 0.88",
    )
    assert "0.86" in p.render()
    assert "hit-rate" in p.render()


def test_posterior_may_not_exceed_gated_tier():
    """Invariant #8: a high posterior against a REFUTED tier is a bug, and caught."""
    appraisal = TargetAppraisal(
        target="X", disease="Y",
        dimensions={},
        composite=_Composite.REFUTED,
        archetype=Archetype.ASSOCIATED_NONCAUSAL,
        posterior=Posterior(value=0.9, prior=0.05, prior_source="test"),
        archetype_rationale="...",
        next_experiment="...",
    )
    assert not appraisal.posterior_respects_gate()

    ok = appraisal.model_copy(update={
        "posterior": Posterior(value=0.08, prior=0.05, prior_source="test")
    })
    assert ok.posterior_respects_gate()


def test_unscoped_context_announces_itself():
    """An all-null context is a red flag that must be stated, not hidden."""
    c = Context()
    assert not c.is_scoped()
    assert "unscoped" in c.describe()

    scoped = Context(cell_type="neuron", ancestry="EUR")
    assert scoped.is_scoped()
    assert "neuron" in scoped.describe()


def test_verdict_line_carries_the_full_tuple():
    appraisal = TargetAppraisal(
        target="APP", disease="Alzheimer's",
        context=Context(disease_subtype="early-onset", ancestry="EUR"),
        dimensions={},
        composite=_Composite.LIKELY_CAUSAL,
        archetype=Archetype.UPSTREAM_INITIATOR,
        inus=InusVerdict(necessity=NSAxis.SUPPORTED, sufficiency=NSAxis.REFUTED),
        archetype_rationale="...",
        next_experiment="...",
    )
    line = appraisal.verdict_line()
    assert "upstream_initiator" in line
    assert "necessary_not_sufficient" in line
    assert "early-onset" in line
