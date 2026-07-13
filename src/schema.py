"""
Causal Evidence Appraisal Tool — core schema.

Design principle: every score must decompose back to a citable, inspectable
EvidenceItem with a stated assumption. Nothing enters a tier that cannot be
clicked through to a source.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Dimension(str, Enum):
    """The seven causal questions. Note these are questions, not data types."""

    INTERVENTION = "intervention"      # has anyone done do(X)?
    GENETIC = "genetic"                # is randomization by nature available?
    TEMPORAL = "temporal"              # does target change before outcome?
    MEDIATION = "mediation"            # driver, mediator, or downstream?
    MECHANISM = "mechanism"            # is there a pathway story?
    ASSOCIATION = "association"        # the honest baseline
    ROBUSTNESS = "robustness"          # how fragile are the assumptions?


class EvidenceType(str, Enum):
    """Specific study designs. Ordering within a dimension matters for tiering."""

    # intervention
    HUMAN_RCT = "human_rct"
    HUMAN_CELL_PERTURBATION = "human_cell_perturbation"   # CRISPR KO/KD, Perturb-seq
    ANIMAL_PERTURBATION = "animal_perturbation"

    # genetic
    RARE_PENETRANT_VARIANT = "rare_penetrant_variant"
    PROTECTIVE_ALLELE = "protective_allele"               # weight heaviest
    ALLELIC_SERIES = "allelic_series"                     # dose-response
    MENDELIAN_RANDOMIZATION = "mendelian_randomization"
    GWAS_COLOCALIZATION = "gwas_colocalization"
    GWAS_NEAREST_GENE = "gwas_nearest_gene"               # penalize: a locus, not a target

    # temporal
    LONGITUDINAL_COHORT = "longitudinal_cohort"
    ANCHORED_ONSET_COHORT = "anchored_onset_cohort"       # DIAN-style known clock

    # mediation
    FORMAL_MEDIATION = "formal_mediation"
    PATHWAY_EPISTASIS = "pathway_epistasis"

    # mechanism
    BIOCHEMICAL_PATHWAY = "biochemical_pathway"
    EXPRESSION_CONCORDANCE = "expression_concordance"

    # association
    CROSS_SECTIONAL = "cross_sectional"
    OBSERVATIONAL_COHORT = "observational_cohort"

    # robustness
    REPLICATION = "replication"
    SENSITIVITY_ANALYSIS = "sensitivity_analysis"


class Direction(str, Enum):
    """
    Sign of the causal claim. Bidirectional evidence -- increase harms AND
    decrease protects -- is jointly far stronger than either alone.
    """

    UP_HARMS = "target_up_disease_up"
    DOWN_PROTECTS = "target_down_disease_down"
    UP_PROTECTS = "target_up_disease_down"
    DOWN_HARMS = "target_down_disease_up"
    NULL = "null"


class System(str, Enum):
    """
    What system the evidence came from. Human > model.

    Deliberately generic. Disease-specific model systems (organoids, PDX,
    xenografts, humanized mice) map onto these tiers; the tier is what carries
    causal weight, not the specific model.
    """

    HUMAN = "human"
    HUMAN_PRIMARY_CELL = "human_primary_cell"
    HUMAN_DERIVED_MODEL = "human_derived_model"   # iPSC, organoid, PDX, explant
    ANIMAL_MODEL = "animal_model"
    CELL_LINE = "cell_line"
    IN_SILICO = "in_silico"


class Readout(str, Enum):
    """
    What was measured, ordered by distance from what the patient experiences.

    CLINICAL_OUTCOME is disease-agnostic by construction: it means survival,
    function, symptom burden, or event incidence -- whatever the disease's
    endpoint is. Do not add disease-specific readouts here; put the specific
    measure in EvidenceItem.notes.
    """

    CLINICAL_OUTCOME = "clinical_outcome"        # survival, function, events
    SURROGATE_ENDPOINT = "surrogate_endpoint"    # validated stand-in for outcome
    DISEASE_PATHOLOGY = "disease_pathology"      # histology, imaging, tumor burden
    BIOMARKER = "biomarker"                      # circulating or tissue analyte
    MOLECULAR_PROFILE = "molecular_profile"      # transcriptome, proteome
    CELLULAR_PHENOTYPE = "cellular_phenotype"    # viability, proliferation, function


class Assumption(str, Enum):
    """
    Untestable conditions required for the evidence to license a causal claim.
    Every causal estimate is assumption-conditional. Surfacing which assumption
    is doing the work is the point of the tool.
    """

    NO_UNMEASURED_CONFOUNDING = "no_unmeasured_confounding"
    NO_HORIZONTAL_PLEIOTROPY = "no_horizontal_pleiotropy"          # MR
    INSTRUMENT_RELEVANCE = "instrument_relevance"                  # MR
    EXCLUSION_RESTRICTION = "exclusion_restriction"                # MR / IV
    NO_MEDIATOR_OUTCOME_CONFOUNDING = "no_mediator_outcome_confounding"
    NO_REVERSE_CAUSATION = "no_reverse_causation"
    MODEL_VALIDITY = "model_validity"                              # animal / cell models
    CORRECT_DAG = "correct_dag"
    POSITIVITY = "positivity"
    SUTVA = "sutva"
    MEASURED_SPECIES_IS_ACTIVE_SPECIES = "measured_species_is_active_species"
    NO_SELECTION_BIAS = "no_selection_bias"


class Tier(str, Enum):
    """
    Ordinal, not numeric. A 73/100 implies precision we do not have.

    CONTRADICTED is not "weak" -- it is evidence pointing the other way, and it
    forces the composite down rather than being averaged away.
    """

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    ABSENT = "absent"
    CONTRADICTED = "contradicted"


class Composite(str, Enum):
    """
    Ceiling is set by the strongest causal-evidence tier present.
    Association + mechanism alone caps at UNVALIDATED regardless of strength.
    """

    CAUSAL_DRIVER = "causal_driver"          # requires bidirectional causal evidence
    LIKELY_CAUSAL = "likely_causal"
    PLAUSIBLE = "plausible"
    UNVALIDATED = "unvalidated"              # ceiling for assoc/mechanism-only
    LIKELY_NONCAUSAL = "likely_noncausal"
    REFUTED = "refuted"


class NecessitySufficiency(str, Enum):
    """
    The INUS sub-field (docs/memo.md). ORTHOGONAL to position: a driver or mediator
    ALSO occupies one of these boxes, and the box decides the therapeutic
    implication.

    Necessity is probed by loss-of-function (does the phenotype fail without X?).
    Sufficiency is probed by gain-of-function in a naive background (does X alone
    produce it?). Different experiments, different axes -- never collapse them.

    necessity != average effect: a strictly necessary factor can have a small
    population-average effect if it is rarely the rate-limiting step.
    """

    NECESSARY_AND_SUFFICIENT = "necessary_and_sufficient"   # monogenic; rare
    NECESSARY_NOT_SUFFICIENT = "necessary_not_sufficient"   # INUS component; gatekeeper
    SUFFICIENT_NOT_NECESSARY = "sufficient_not_necessary"   # one of several routes; stratify
    NEITHER = "neither"                                     # modifier / bystander
    UNDETERMINED = "undetermined"                           # experiments not done


class NSAxis(str, Enum):
    """One arm of the INUS sub-field, scored independently from evidence subtype."""

    SUPPORTED = "supported"          # loss-of-function (necessity) / gain-of-function (sufficiency) shows it
    REFUTED = "refuted"              # the experiment was done and came back negative
    UNTESTED = "untested"


class Archetype(str, Enum):
    """
    The differentiator. A score is forgettable; "your target sits on no causal
    path despite strong association" is not.

    Values are STRUCTURAL, not exemplar-named. The archetype describes a shape
    in the dimension vector, and that shape is disease-agnostic. Exemplars
    (HDL, tau, amyloid) appear only in rationale text as illustrations, and
    only when the disease area makes them legible to the reader.

    A cancer researcher should never be told their target has "the tau pattern."
    """

    # Strong association, null genetic, null intervention. Sits on no causal path.
    # Exemplars: HDL-C in CVD; homocysteine in CVD.
    ASSOCIATED_NONCAUSAL = "associated_noncausal"

    # Target correlates, but the causal signal sits on an upstream node in the
    # same pathway. Requires pathway context to detect.
    # Exemplars: CRP vs IL-6 in CVD.
    DISPLACED_SIGNAL = "displaced_signal"

    # Strong genetic causal support, weak concurrent correlation, often plateaus.
    # Correlation decays with causal distance, so initiators correlate poorly.
    # Exemplars: amyloid in AD; LDL exposure duration in CVD.
    UPSTREAM_INITIATOR = "upstream_initiator"

    # Strong association and plausible mediator position, weak independent
    # genetic support. Excellent biomarker; uncertain target. A mediator IS causal.
    # Exemplars: tau in AD.
    DOWNSTREAM_MEDIATOR = "downstream_mediator"

    # Changes only after onset. Cannot be driving what precedes it.
    REACTIVE_CONSEQUENCE = "reactive_consequence"

    # Mechanism only. Evidence of nothing -- not evidence against.
    UNTESTED = "untested"

    # Converging bidirectional causal evidence plus successful human intervention.
    # Exemplars: PCSK9 in CVD; BCR-ABL in CML; HER2 in breast cancer.
    VALIDATED_DRIVER = "validated_driver"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


class EffectSize(BaseModel):
    """Effect with uncertainty. Confidence is tracked separately from magnitude:
    'confident it is small' and 'no idea if it is large' are different states."""

    value: float
    ci_low: Optional[float] = None
    ci_high: Optional[float] = None
    units: str = Field(description="e.g. 'OR per SD', 'hazard ratio', 'log2FC'")

    @property
    def is_null(self) -> bool:
        """CI crosses the null. Units determine whether null is 0 or 1."""
        if self.ci_low is None or self.ci_high is None:
            return False
        null_value = 1.0 if any(
            u in self.units.lower() for u in ("or", "hr", "rr", "ratio")
        ) else 0.0
        return self.ci_low <= null_value <= self.ci_high

    @property
    def is_precise(self) -> bool:
        """Do we have an interval at all? Absence of CI is itself information."""
        return self.ci_low is not None and self.ci_high is not None


class EvidenceItem(BaseModel):
    """
    The atomic unit. Every tier decomposes into these; every one must be
    clickable through to a source.

    Curation note: effect sizes and citations are hand-curated from papers
    actually read. A hallucinated PMID would undercut the entire
    assumption-forward thesis of the tool.
    """

    id: str
    target: str
    disease: str

    dimension: Dimension
    evidence_type: EvidenceType
    direction: Direction
    effect: Optional[EffectSize] = None

    system: System
    readout: Readout

    assumptions_required: list[Assumption] = Field(
        default_factory=list,
        description="What must hold for this to license a causal claim",
    )
    falsified_by: list[str] = Field(
        default_factory=list,
        description="Plain-language: what result would kill this item",
    )

    source: str = Field(description="DOI or PMID. Required. No exceptions.")
    provenance_group: str = Field(
        description=(
            "Ten papers citing one original observation is ONE piece of evidence. "
            "Items sharing a provenance_group are de-duplicated before scoring."
        )
    )
    contradicts: list[str] = Field(
        default_factory=list, description="ids of EvidenceItems this conflicts with"
    )

    notes: Optional[str] = None

    @field_validator("source")
    @classmethod
    def source_must_look_real(cls, v: str) -> str:
        if not (v.startswith("10.") or v.upper().startswith("PMID:")):
            raise ValueError(
                "source must be a DOI (10.xxxx/...) or PMID:xxxxxxx. "
                "Uncited evidence does not enter the ledger."
            )
        return v


class DimensionAssessment(BaseModel):
    """One dimension's verdict, with everything needed to defend it."""

    dimension: Dimension
    tier: Tier
    items: list[EvidenceItem]

    assumptions_load_bearing: list[Assumption] = Field(
        default_factory=list,
        description="Which assumptions, if violated, would change this tier",
    )
    contradicting_items: list[EvidenceItem] = Field(
        default_factory=list, description="Surfaced, never averaged away"
    )
    falsifiability: str = Field(
        default="", description="What would drop this tier"
    )

    @property
    def has_bidirectional_support(self) -> bool:
        """increase→harm AND decrease→protect. The strongest signal available."""
        dirs = {i.direction for i in self.items}
        return bool(
            {Direction.UP_HARMS, Direction.DOWN_PROTECTS} <= dirs
            or {Direction.UP_PROTECTS, Direction.DOWN_HARMS} <= dirs
        )


class Context(BaseModel):
    """
    The conditional scope. The atomic claim is `A -> B | context`, never a bare
    "A causes B". Every slot may be null; a null slot means "unspecified / not
    scoped", NOT "any". Generalization beyond the observed context is flagged,
    never assumed.
    """

    cell_type: Optional[str] = None          # CL / Uberon term
    tissue: Optional[str] = None
    background: Optional[str] = None          # genetic background
    ancestry: Optional[str] = None
    sex: Optional[str] = None
    disease_subtype: Optional[str] = None
    stage: Optional[str] = None               # developmental / disease stage
    dose: Optional[str] = None
    time: Optional[str] = None

    def is_scoped(self) -> bool:
        """True if any slot is filled. An all-null context is a red flag, not a win."""
        return any(v is not None for v in self.model_dump().values())

    def describe(self) -> str:
        filled = {k: v for k, v in self.model_dump().items() if v is not None}
        if not filled:
            return "unscoped (no context specified -- verdict is not context-conditional)"
        return ", ".join(f"{k}={v}" for k, v in filled.items())


class InusVerdict(BaseModel):
    """
    The necessity x sufficiency sub-field, carried alongside the position label.

    Necessity and sufficiency are scored on SEPARATE axes (loss-of-function vs
    gain-of-function evidence) and only then combined into a box. Keeping the two
    arms visible is the point -- the two middle boxes look identical in a naive
    correlation but have opposite therapeutic meaning.
    """

    necessity: NSAxis = NSAxis.UNTESTED
    sufficiency: NSAxis = NSAxis.UNTESTED

    @property
    def box(self) -> NecessitySufficiency:
        n, s = self.necessity, self.sufficiency
        if n == NSAxis.SUPPORTED and s == NSAxis.SUPPORTED:
            return NecessitySufficiency.NECESSARY_AND_SUFFICIENT
        if n == NSAxis.SUPPORTED and s == NSAxis.REFUTED:
            return NecessitySufficiency.NECESSARY_NOT_SUFFICIENT
        if n == NSAxis.REFUTED and s == NSAxis.SUPPORTED:
            return NecessitySufficiency.SUFFICIENT_NOT_NECESSARY
        if n == NSAxis.REFUTED and s == NSAxis.REFUTED:
            return NecessitySufficiency.NEITHER
        return NecessitySufficiency.UNDETERMINED

    @property
    def therapeutic_note(self) -> str:
        b = self.box
        if b == NecessitySufficiency.NECESSARY_NOT_SUFFICIENT:
            return (
                "Necessary component (INUS / gatekeeper). Perturbing it shifts risk "
                "without abolishing disease; expect to need combination or upstream "
                "intervention. Loss-of-function reduces but does not eliminate."
            )
        if b == NecessitySufficiency.SUFFICIENT_NOT_NECESSARY:
            return (
                "Driver for the subgroup it actually drives; absent in many patients. "
                "The honest verdict is stratified -- 'driver for the X-defined subtype'."
            )
        if b == NecessitySufficiency.NECESSARY_AND_SUFFICIENT:
            return "Monogenic-like: alone required and enough. Rare."
        if b == NecessitySufficiency.NEITHER:
            return "Modifier, passenger, or bystander on this axis."
        return "Necessity/sufficiency not established; loss- and gain-of-function needed."


class Posterior(BaseModel):
    """
    The subordinate confidence estimate. Governed by three hard rules from DESIGN:
      1. it may NEVER exceed the gated tier (a posterior cannot overrule identification);
      2. until calibrated, it renders as a band/bin, never a bare float;
      3. it shows digits only when calibrated, and then WITH reliability provenance.

    `render()` enforces rule 2/3. Do not read `.value` for display -- use render().
    """

    value: float = Field(ge=0.0, le=1.0)
    prior: float = Field(ge=0.0, le=1.0, description="Base rate used; report it explicitly")
    prior_source: str = Field(description="Where the prior came from (curated set? constraint? network distance?)")
    calibrated: bool = False
    reliability_bin: Optional[str] = Field(
        default=None,
        description="e.g. '0.9 bin, observed hit-rate 0.88 on ClinGen gold set'",
    )

    def render(self) -> str:
        """The only display path. Bare floats are forbidden pre-calibration."""
        if not self.calibrated:
            if self.value >= 0.66:
                band = "likely causal"
            elif self.value >= 0.33:
                band = "uncertain"
            else:
                band = "likely non-causal"
            return f"{band}, uncalibrated (prior {self.prior:.2f} from {self.prior_source})"
        prov = self.reliability_bin or "calibrated, provenance missing"
        return f"{self.value:.2f} ({prov})"


class TargetAppraisal(BaseModel):
    """
    The full output. The composite tier is the headline; the posterior is
    subordinate to it. The verdict is a (position, necessity/sufficiency, context)
    tuple, never a bare global label.
    """

    target: str
    disease: str
    context: Context = Field(
        default_factory=Context,
        description="The conditional scope. An unscoped verdict must say so.",
    )

    dimensions: dict[Dimension, DimensionAssessment]

    # --- the verdict tuple ---
    composite: Composite                       # gated ordinal tier -- the HEADLINE
    archetype: Archetype                        # position label
    inus: InusVerdict = Field(default_factory=InusVerdict)   # necessity x sufficiency sub-field
    posterior: Optional[Posterior] = None       # subordinate; may be None until scored

    archetype_rationale: str
    next_experiment: str = Field(
        description=(
            "Which dimension is weakest and most cheaply strengthened. "
            "This converts the tool from a scorer into a decision aid."
        )
    )

    # --- transparency fields (DESIGN invariant #4) ---
    not_examined: list[Dimension] = Field(
        default_factory=list,
        description="Modalities not queried. Never silently truncate.",
    )
    stopped_because: Optional[str] = None
    conflicts: list[str] = Field(
        default_factory=list,
        description="Directional disagreements, surfaced not averaged (invariant #5)",
    )
    coarse_label_warning: bool = Field(
        default=False,
        description="Disease term maps to many subtypes; stratification advised.",
    )

    known_limitations: list[str] = Field(
        default_factory=lambda: [
            "Effect depends on when you intervene; a static tier has no time axis.",
            "Driver and mediator are both causal; position is a relation, not a coordinate.",
            "Total and direct effects diverge; conditioning on a mediator can induce collider bias.",
            "Subgroup causality: a target causal only in a molecular subset needs (target, disease, subgroup) as the unit.",
        ]
    )

    def posterior_respects_gate(self) -> bool:
        """
        DESIGN invariant #8: the posterior may never exceed the gated tier.
        A high posterior against a REFUTED/UNVALIDATED composite is a bug.
        Returns True when consistent (or when no posterior is set).
        """
        if self.posterior is None:
            return True
        ceiling = {
            Composite.CAUSAL_DRIVER: 1.00,
            Composite.LIKELY_CAUSAL: 0.90,
            Composite.PLAUSIBLE: 0.66,
            Composite.UNVALIDATED: 0.50,
            Composite.LIKELY_NONCAUSAL: 0.33,
            Composite.REFUTED: 0.10,
        }[self.composite]
        return self.posterior.value <= ceiling

    def verdict_line(self) -> str:
        """One-line human summary: position | INUS box | scope | confidence."""
        conf = self.posterior.render() if self.posterior else "confidence not scored"
        return (
            f"{self.archetype.value} [{self.inus.box.value}] "
            f"| scope: {self.context.describe()} "
            f"| tier: {self.composite.value} | {conf}"
        )

    def causal_evidence_present(self) -> bool:
        """Association and mechanism do not count. This gates the ceiling."""
        causal_dims = (
            Dimension.INTERVENTION,
            Dimension.GENETIC,
            Dimension.TEMPORAL,
            Dimension.MEDIATION,
        )
        return any(
            self.dimensions[d].tier in (Tier.STRONG, Tier.MODERATE)
            for d in causal_dims
            if d in self.dimensions
        )
