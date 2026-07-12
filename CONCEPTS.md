# Concepts

*The conceptual reference for the tool. `DESIGN.md` is what to build; this is why
the causal reasoning is shaped the way it is. Disease-agnostic throughout —
worked examples are drawn from areas where the field has already paid for the
answer, and are illustrations, not scope.*

---

## The one-sentence thesis

**Correlation-with-outcome and causal-position are orthogonal axes.** Every
failure mode below — marker, bystander, reactive consequence, displaced signal —
is a different way of scoring high on the first axis while scoring zero on the
second. The field routinely collapses the two into one number, and the cost is
measured in decades and drug programs. The tool exists to keep them apart.

A structural fact underwrites this: in any chain `Driver → Mediator → Outcome`,
noise accumulates at each edge, so the mediator always correlates *more tightly*
with the outcome than the driver does. **Correlation decays with causal distance.**
Ranking candidates by correlation therefore ranks proximate causes above
initiating ones — systematically, as arithmetic, not as a bug.

---

## The classification vocabulary

The ways a factor can relate to a disease. The distinctions are about *position
in the causal graph*, which a scalar score cannot fully express — the vocabulary
carries what a number cannot.

**Driver** — causally initiates or sustains the disease. Perturbing it changes
the outcome. The thing you want to target.
*Exemplars: PCSK9 in CVD; BCR-ABL in CML.*

**Mediator** — sits *on* the causal path between a driver and the outcome. A
mediator **is causal**: intervening on it changes the outcome. It is not a lesser
category, it is a different position. Mediators correlate *better* with outcome
than drivers do, which is exactly what makes them seductive as false targets.
*Exemplar: tau in AD, plausibly.*

**Marker** — correlates with disease but sits on **no causal path at all**.
Intervening does nothing. The expensive trap.
*Exemplar: HDL-C in CVD.*

**Bystander** — correlates because it shares an upstream common cause with the
disease (Reichenbach's common cause), but neither causes nor is caused by it.
Distinct from a marker: a marker may be downstream of the disease; a bystander is
off to the side, linked only through a confounder.

**Reactive consequence** — changes only *after* onset. Downstream of the disease,
not upstream. Reverse causation. Cannot drive what precedes it.
*Exemplar: acute-phase reactants, across essentially every disease.*

**Displaced signal (wrong node)** — the target correlates, but the causal signal
lives one node upstream in the same pathway. You are targeting the reporter, not
the source. Only detectable *with pathway context* — never from the target's own
evidence.
*Exemplar: CRP in CVD, when IL-6 is the real driver.*

**Upstream initiator** — genuinely causal, but early and often self-limiting, so
its *concurrent* correlation with disease severity is weak. Low correlation here
is not evidence against causality — it is the signature of an initiator.
*Exemplars: amyloid in AD; HPV in cervical cancer; cumulative LDL exposure in CVD.*

---

## What breaks when causal-inference rules are ported to biology

The formal frameworks — Pearl's do-calculus and DAGs, the Rubin potential-outcomes
model, Bradford Hill's viewpoints — were built for single-exposure epidemiology.
Six things mis-transfer to molecular biology, and each needs explicit handling.

### 1. Pleiotropy — the causal unit is not the gene

One gene, but different specific perturbations route to different diseases.
Variants at one locus can be causal in opposite directions, or cause unrelated
diseases. The causal unit is a **(specific perturbation × pathway × cellular
context)** triple, not "the gene."

Two consequences:
- Do not credit "the gene." Credit the specific molecular change.
- In Mendelian randomization, **horizontal pleiotropy** — the instrument affecting
  the outcome through a second path — *breaks the method* and must be tested
  (MR-Egger intercept, weighted median, outlier detection).

*Illustration: at the APP locus, cleavage-site mutations cause AD while the A673T
allele is protective; MAPT mutations cause FTD, not AD. Same gene, divergent
causal consequences.*

### 2. Necessity vs. sufficiency — two experiments, two claims

- **Necessity:** can the disease happen without X? → loss-of-function. If disease
  disappears when X is removed, X was necessary.
- **Sufficiency:** does X alone produce disease? → gain-of-function in a naive
  background. If disease appears, X was sufficient.

A factor can be one without the other. Most common disease is a **collection of
sufficient-but-not-necessary drivers**, so the honest output is a *set* of
context-scoped drivers with attributable weight, not a single cause.

And **necessity ≠ average effect**: a strictly necessary factor can have a *small*
population-average effect if it is rarely the rate-limiting step.

### 3. Feedback loops break "upstream / downstream"

Biology has cycles. DAGs are acyclic by definition. Inside a loop, "driver vs.
mediator" stops being well-defined — the classification vocabulary quietly assumes
a direction the biology does not have. Flag likely-cyclic relationships rather than
forcing a linear label onto them.

### 4. Bystanders that look causal — the confounding structure is enormous

Disease state is a **common cause** driving thousands of molecular changes at once,
so they are all mutually correlated while most are causally inert. Naive
observational effect-estimation on a reactive node can even return a *spurious*
causal signal.

This is why network-level "which change is causal?" is the hardest question, and
why **perturbation** (CRISPR screens, Perturb-seq — `do(X)` by construction) is the
real arbiter. A reactive node, when perturbed, does not move the outcome; a causal
one does.

### 5. Reverse causation — the signature biological trap

Cross-sectional molecular data cannot distinguish "gene drove disease" from
"disease drove gene." **Temporal ordering** is the discriminator, and genetics
provides it for free: genotype is fixed at conception, so the arrow can only point
away from it. This is the logic behind Mendelian randomization.

### 6. Bradford Hill needs re-derivation, not adoption

Four of the nine viewpoints mis-transfer:

- **Specificity** — one-cause-one-disease is false for common disease (most
  "diseases" are collections of mechanistically distinct conditions). Reframe as
  **perturbation specificity**: did the intervention hit only the intended target?
  On/off-target and rescue controls. This becomes a data-quality gate, not a
  causal criterion.
- **Reversibility** — weak in epidemiology, but in biology it is one of the
  **strongest** available tests: remove the factor and the phenotype goes; restore
  it and the phenotype returns. This re-runs the causal contrast inside a single
  system. **Promote it.**
- **Plausibility** — the dangerous one. A mechanism story is *the exact thing that
  makes a false causal claim feel true*. It must be a **tiebreaker only**, never
  primary evidence. The architecture must make it impossible for a mechanism
  narrative to raise a causal score on its own.
- **Analogy** — near-purely rhetorical. ~Zero causal weight; keep only as a
  hypothesis-generation note.

---

## Two load-bearing principles

### Direction cannot come from your most abundant data

Cross-sectional co-expression carries **zero** directional information — it cannot
distinguish A→B from B→A from Z→both. Direction comes *only* from:

- **genetics** (a natural experiment; the arrow points away from fixed genotype),
- **temporal ordering** (longitudinal data, pseudotime with heavy caveats), or
- **perturbation** (the do-operator gives direction natively).

**Hard rule:** correlational data contributes to *strength* and *consistency* at
most, and **never** to *direction*. This is enforced in the scorer, not left as a
footnote.

### Population ≠ individual; mechanism and statistics come apart

An average causal effect is not a mechanism, and a population-average effect can
point the *opposite* way from a given patient's (Simpson's paradox is the
population-scale version of this). Individual causality is never observed directly
— only inferred — so it is the **asymptote** the tool climbs toward by conditioning
ever more finely (population → subgroup → biomarker-defined microstratum → N-of-1),
trading statistical power for individual relevance at each step. Never leap to it.

**Subgroup causality is real.** A target can be causal in a molecularly defined
subset and inert elsewhere. A single verdict per target–disease pair cannot express
this; where the biology demands it, the unit becomes `(target, disease, subgroup)`.
*Illustration: HER2 is causal in the amplified subset, not outside it.*

---

## The evidence hierarchy for direction

The spine everything else hangs on, strongest to weakest:

```
intervention in humans
  > natural experiment (genetics)
    > temporal ordering with adjustment
      > cross-sectional adjustment
        > raw association
          > mechanistic plausibility alone
```

The single most important asymmetry: **interventions establish causation;
observations at best identify it under untestable assumptions.** Every method below
the top is a different way of manufacturing, or credibly borrowing, the
counterfactual comparison that observation alone can never supply.

---

## The seven dimensions

Each maps to a **distinct causal question**, not a data type. That is the
discipline: "genetics" is a data type; "is there a natural experiment?" is a
question, and the same data type can answer different questions with very different
causal force.

| # | Dimension | The question it answers | What populates it |
|---|---|---|---|
| 1 | **Interventional** | Has anyone done *do(X)*? | Human RCT > human-cell perturbation (CRISPR, Perturb-seq) > animal. Encode system, readout, and whether the effect went the predicted direction. |
| 2 | **Genetic** | Is randomization by nature available? | Rare penetrant variants; allelic series (dose-response); **protective alleles — weight heaviest, they give bidirectional control**; MR with pleiotropy tests; GWAS + colocalization. Penalize "nearest gene to a hit" — a locus is not a target. |
| 3 | **Temporal** | Does the target change *before* the outcome? | Longitudinal data, ideally anchored to a known onset clock. The primary reverse-causation discriminator. |
| 4 | **Mediation / position** | Driver, mediator, or downstream? | Is it on the path from a known driver? Formal mediation (direct/indirect effects) with sensitivity analysis for mediator–outcome confounding. |
| 5 | **Mechanistic plausibility** | Is there a pathway story? | Biochemistry; cell-type/tissue concordance. **The weakest dimension — the one that makes false targets feel true.** Tiebreaker only; can never raise the score alone. |
| 6 | **Association strength** | The honest baseline | Correlation with disease. Displayed *separately*, never drives the composite. Strong here + null everywhere else is a red flag, not a high score. |
| 7 | **Robustness / fragility** | How much must we assume? | E-value / Rosenbaum bounds (how much unmeasured confounding nullifies it?); replication; cross-modality agreement; **contradictory evidence logged, not buried.** |

---

## The scoring rules that hold it together

- **Gate, don't sum.** The dimensions are not commensurable. A beautiful mechanism
  cannot substitute for an intervention. This is the rule that would have stopped
  the CETP-inhibitor programs.
- **The ceiling is set by the strongest causal-evidence tier present.** Association
  + mechanism alone caps at "unvalidated," no matter how strong.
- **Bidirectional evidence unlocks the top tier.** Increase-harms AND
  decrease-protects is jointly far stronger than either alone. Track sign.
- **Contradiction forces the composite down** and is surfaced, never averaged away.
  A genetics-vs-perturbation disagreement is often the most informative thing in
  the report.
- **De-duplicate by provenance.** Ten papers citing one original observation is one
  piece of evidence.
- **Ordinal, not numeric.** A 73/100 implies precision the evidence does not
  support. Tiers: strong / moderate / weak / absent / contradicted.

---

## The two sharpest points, for compression

If reducing to a single slide:

1. **The hierarchy for direction:** intervention > natural experiment (genetics) >
   temporal ordering > cross-sectional adjustment > raw association > mechanism
   alone. Everything else is detail on this spine.

2. **The thesis:** correlation-with-outcome and causal-position are orthogonal, and
   every failure mode — marker, bystander, reactive consequence, displaced signal —
   is a different way of scoring high on the first axis while scoring zero on the
   second.
