# Concepts

> 🧭 **Understand — the causal framework.** *Why* the scoring is shaped the way it is (Bradford Hill + Pearl, re-derived for biology). For the *why-it-exists*, read [memo.md](memo.md) first; for *what shipped*, see [IMPLEMENTATION.md](docs/IMPLEMENTATION.md). Full map: **[docs/README.md](docs/README.md)**.

*This is the conceptual reference — the reasoning behind how the tool scores
evidence. It is disease-agnostic; the worked examples come from areas where the
field has already paid dearly for the answer, and they are illustrations, not
scope.*

---

## Why I think the reasoning has to be shaped this way

I have spent most of my career watching careful people measure an association and
then, a sentence later, narrate it as causation. I do not say that to scold anyone
— I have done it myself, and I got a bit naive about how much a good mechanism
story could settle. The cost of the mistake is not abstract. In Alzheimer's disease
the clinical trial failure rate has run north of 90%, and a large share of those
programs chased nodes that correlated beautifully with the disease and turned out
not to drive it.

The single experience that reshaped how I think about all of this came from
Huntington's disease. We had assumed, from fixed snapshots, that the mutant
huntingtin inclusion body was toxic, because neurons with inclusions were sicker.
When we finally followed individual neurons over time instead of comparing
snapshots, the picture inverted: forming an inclusion often predicted *better*
survival. The abnormality that correlated with disease was, at least in part, a
coping response. I do not think there is even a clean name for that bias — it is
close to survivorship bias but not the same thing — and it is everywhere in
disease biology. So the reasoning below is built to keep me from making that
mistake again, and to make it hard for anyone using the tool to make it either.

Let me start with the one idea everything hangs on, then walk through where the
textbook rules break when you carry them into molecular biology, and how I would
handle each break.

---

## The one idea: correlation with outcome and causal position are different axes

If you take away one thing, take this. **How tightly a factor correlates with an
outcome and where it sits on the causal path are two different axes.** Every failure
mode I list below — marker, bystander, reactive consequence, displaced signal — is a
different way of scoring high on the first axis while scoring zero on the second.
The field routinely collapses the two into a single number, and that is exactly
where the decades and the drug programs go.

There is a structural reason this is not a rare accident but the default. In any
chain `Driver → Mediator → Outcome`, noise is added at every edge, so the mediator
always correlates *more tightly* with the outcome than the driver does. In other
words, **correlation decays with causal distance.** Rank your candidates by
correlation and you will systematically rank proximate causes above the initiating
ones — not as a bug, but as arithmetic. That is worth sitting with, because it means
the most seductive-looking target is often the wrong one.

---

## A vocabulary for where a factor sits

A scalar score cannot express position in a causal graph, so I lean on a small
vocabulary. The distinctions are about *where the factor sits*, and they carry what
a number cannot.

A **driver** causally initiates or sustains the disease; perturb it and the outcome
moves. That is the thing you want to target. For example, PCSK9 in cardiovascular
disease, or BCR-ABL in CML.

A **mediator** sits *on* the path between a driver and the outcome. I want to be
careful here, because this is where people get hurt: a mediator **is causal** —
intervening on it does change the outcome — so it is not a lesser category, just a
different position. And because it is closer to the outcome, it correlates *better*
than the driver does, which is precisely what makes it seductive as a false target.
Tau in Alzheimer's is plausibly a mediator, and its tight correlation with cognitive
decline is exactly the kind of signal I have learned to distrust on its own.

A **marker** correlates with the disease but sits on **no causal path at all** —
intervene and nothing happens. That is the expensive trap; HDL cholesterol in
cardiovascular disease is the one the field paid for.

A **bystander** correlates because it shares an upstream common cause with the
disease — Reichenbach's common cause — but neither causes it nor is caused by it. I
keep it distinct from a marker: a marker can be downstream of the disease, whereas a
bystander sits off to the side, linked only through a confounder.

A **reactive consequence** changes only *after* onset. It is downstream of the
disease, reverse causation, and it cannot be driving what precedes it. Acute-phase
reactants do this across essentially every disease. This is the category where my
Huntington's experience makes me most cautious, because a reactive change can be a
coping response that correlates with severity while being protective, not
pathogenic.

A **displaced signal**, or wrong node, correlates, but the causal signal lives one
node upstream in the same pathway — you are measuring the reporter, not the source.
The important and humbling point is that you cannot detect this from the target's own
evidence; it takes pathway context. CRP in cardiovascular disease is the example,
when IL-6 is the real driver.

An **upstream initiator** is genuinely causal but early, and often self-limiting, so
its *concurrent* correlation with disease severity is weak. I want to flag this one
loudly: low correlation here is not evidence against causality — it is the
*signature* of an initiator. Amyloid in Alzheimer's is the contested example; HPV in
cervical cancer and cumulative LDL exposure in cardiovascular disease are cleaner
ones. Amyloid changes decades before symptoms and then plateaus, which is exactly
what an early initiator looks like, and exactly what a naive correlation would
underweight.

---

## Where the textbook rules break when ported to biology

The formal frameworks — Pearl's do-calculus and DAGs, the Rubin potential-outcomes
model, Bradford Hill's viewpoints — were built for single-exposure epidemiology, and
I have a lot of respect for them. But six things mis-transfer to molecular biology,
and each needs explicit handling rather than faith.

**1. Pleiotropy — the causal unit is not the gene.** One gene, but different
specific perturbations route to different diseases, sometimes in opposite
directions. So I do not credit "the gene"; I credit the specific molecular change —
the **(specific perturbation × pathway × cellular context)** triple. For example, at
the APP locus the cleavage-site mutations cause Alzheimer's while the A673T allele is
protective, and MAPT mutations cause frontotemporal dementia, not Alzheimer's. Same
gene, divergent causal consequences. This has a hard methodological edge, too: in
Mendelian randomization, horizontal pleiotropy — the instrument reaching the outcome
through a second path — *breaks the method*, so it has to be tested (MR-Egger
intercept, weighted median, outlier detection), not assumed away.

**2. Necessity versus sufficiency — two experiments, two claims.** Necessity asks
whether the disease can happen without X, and you probe it by loss-of-function: take
X away and see whether the disease disappears. Sufficiency asks whether X alone
produces disease, and you probe it by gain-of-function in a naive background. A
factor can be one without the other, and I think most common disease is a
*collection* of sufficient-but-not-necessary drivers, so the honest output is a
*set* of context-scoped drivers with attributable weight, not a single cause. One
more subtlety I do not want to muddy but cannot leave out: necessity is not the same
as average effect. A strictly necessary factor can have a small population-average
effect if it is rarely the rate-limiting step.

**3. Feedback loops break "upstream versus downstream."** Biology has cycles; DAGs
are acyclic by definition. Inside a loop, "driver versus mediator" quietly stops
being well-defined — the vocabulary assumes a direction the biology does not have.
Where I suspect a cycle, I would rather flag it than force a linear label onto it.

**4. Bystanders that look causal — the confounding structure here is enormous.** The
disease state is itself a common cause driving thousands of molecular changes at
once, so they are all mutually correlated while most are causally inert. Naive
observational effect-estimation on a reactive node can even hand you a *spurious*
causal signal. This is why "which change is causal?" is the hardest question at the
network level, and why I put so much weight on **perturbation** — CRISPR screens,
Perturb-seq, `do(X)` by construction. Perturb a reactive node and the outcome does
not move; perturb a causal one and it does. That is the arbiter.

**5. Reverse causation — the signature biological trap.** Cross-sectional molecular
data simply cannot tell "gene drove disease" from "disease drove gene." Temporal
ordering is the discriminator, and genetics gives it to us for free, because
genotype is fixed at conception, so the arrow can only point away from it. That is
the logic underneath Mendelian randomization, and it is why I trust a natural
experiment over a beautiful cross-sectional dataset.

**6. Bradford Hill needs re-derivation, not adoption.** I want to be humble here —
these viewpoints have served for decades — but four of the nine do not carry over
cleanly, so I would broaden them a bit. *Specificity*, the one-cause-one-disease
idea, is false for common disease, since most "diseases" are collections of
mechanistically distinct conditions; I reframe it as **perturbation specificity** —
did the intervention hit only the intended target, with on/off-target and rescue
controls — which makes it a data-quality gate, not a causal criterion.
*Reversibility* is weak in epidemiology but one of the *strongest* tests we have in
biology — remove the factor and the phenotype goes, restore it and the phenotype
returns, which re-runs the causal contrast inside a single system — so I promote it.
*Plausibility* is the dangerous one, and I will say it plainly: a mechanism story is
the exact thing that makes a false causal claim feel true. It has to be a tiebreaker
only, never primary evidence, and the architecture has to make it *impossible* for a
narrative to raise a causal score on its own. *Analogy* is nearly pure rhetoric — I
keep it only as a hypothesis-generation note.

---

## Two principles I will not compromise on

**Direction cannot come from your most abundant data.** Cross-sectional
co-expression is what we have the most of, and it carries **zero** directional
information — it cannot distinguish A→B from B→A from Z→both. Direction comes only
from genetics (the arrow points away from fixed genotype), from temporal ordering
(longitudinal data, or pseudotime with heavy caveats), or from perturbation (the
do-operator gives direction natively). So the hard rule, enforced in the scorer and
not left as a footnote, is that correlational data can contribute to *strength* and
*consistency* at most, and *never* to *direction*. This is the principle my
Huntington's snapshots taught me the hard way: the data you have the most of is the
data least able to tell you which way the arrow points.

**Population is not the individual, and mechanism and statistics come apart.** An
average causal effect is not a mechanism, and a population-average effect can point
the *opposite* way from a given patient's — Simpson's paradox is just the
population-scale version of that. Individual causality is never observed directly,
only inferred, so I treat it as the asymptote the tool climbs toward by conditioning
ever more finely — population, then subgroup, then biomarker-defined microstratum,
then N-of-1 — trading statistical power for individual relevance at each step. I do
not leap to it. And subgroup causality is real: a target can be causal in a
molecularly defined subset and inert everywhere else, so where the biology demands
it the unit becomes `(target, disease, subgroup)`. For example, HER2 is causal in
the amplified subset and not outside it, and a single verdict per target–disease pair
cannot express that.

---

## The hierarchy for direction

Everything else hangs on this spine, strongest to weakest:

```
intervention in humans
  > natural experiment (genetics)
    > temporal ordering with adjustment
      > cross-sectional adjustment
        > raw association
          > mechanistic plausibility alone
```

The asymmetry that matters most: **interventions establish causation; observations,
at best, identify it under untestable assumptions.** Every method below the top rung
is a different way of manufacturing, or credibly borrowing, the counterfactual
comparison that observation alone can never supply. When I read a claim, the first
question I ask is which rung its evidence actually reaches — not how large the effect
is, but how the counterfactual was obtained.

---

## The seven dimensions the tool actually scores

Each dimension maps to a *distinct causal question*, not to a data type. That
distinction is the whole discipline: "genetics" is a data type, but "is there a
natural experiment?" is a question, and the same data type can answer different
questions with very different causal force.

| # | Dimension | The question it answers | What populates it |
|---|---|---|---|
| 1 | **Interventional** | Has anyone done *do(X)*? | Human RCT > human-cell perturbation (CRISPR, Perturb-seq) > animal. Encode system, readout, and whether the effect went the predicted direction. |
| 2 | **Genetic** | Is randomization by nature available? | Rare penetrant variants; allelic series (dose-response); **protective alleles — I weight these heaviest, because they give bidirectional control**; MR with pleiotropy tests; GWAS plus colocalization. Penalize "nearest gene to a hit" — a locus is not a target. |
| 3 | **Temporal** | Does the target change *before* the outcome? | Longitudinal data, ideally anchored to a known onset clock. The primary reverse-causation discriminator. |
| 4 | **Mediation / position** | Driver, mediator, or downstream? | Is it on the path from a known driver? Formal mediation (direct/indirect effects) with sensitivity analysis for mediator–outcome confounding. |
| 5 | **Mechanistic plausibility** | Is there a pathway story? | Biochemistry; cell-type/tissue concordance. **The weakest dimension — the one that makes false targets feel true.** Tiebreaker only; it can never raise the score alone. |
| 6 | **Association strength** | The honest baseline | Correlation with disease. Shown *separately*, and it never drives the composite. Strong here with null everywhere else is a red flag, not a high score. |
| 7 | **Robustness / fragility** | How much must we assume? | E-value / Rosenbaum bounds (how much unmeasured confounding would nullify it?); replication; cross-modality agreement; **contradictory evidence logged, not buried.** |

---

## The rules that hold the scoring together

**Gate, do not sum.** The dimensions are not commensurable, and a beautiful
mechanism cannot substitute for an intervention. This is the single rule that would
have stopped the CETP-inhibitor programs, and if you find yourself adding a mechanism
score to a genetics score, stop.

**The ceiling is set by the strongest causal-evidence tier present.** Association
plus mechanism alone caps at "unvalidated," no matter how strong either one looks.

**Bidirectional evidence unlocks the top tier.** Increase-harms *and*
decrease-protects together is far stronger than either alone, so track the sign, do
not just track magnitude.

**Contradiction forces the composite down, and it is surfaced, never averaged
away.** A genetics-versus-perturbation disagreement is often the most informative
line in the whole report; I would never want it smoothed out.

**De-duplicate by provenance.** Ten papers citing one original observation is one
piece of evidence, not ten.

**Ordinal, not numeric.** A 73/100 implies a precision the evidence does not
support. I prefer tiers — strong, moderate, weak, absent, contradicted — because
they promise only what we can actually deliver.

---

## If I had one slide

Two points, and everything else is detail hanging off them.

First, the hierarchy for direction: intervention, then natural experiment
(genetics), then temporal ordering, then cross-sectional adjustment, then raw
association, then mechanism alone. Ask of any claim only which rung it reaches.

Second, the thesis: correlation-with-outcome and causal-position are different axes,
and every failure mode — marker, bystander, reactive consequence, displaced signal —
is a way of scoring high on the first while scoring zero on the second.

At the end of the day, we desperately need to stop spending decades and fortunes on
factors that correlate with disease but do not drive it. That is the whole reason
this reasoning is built the way it is. Onward and upward.
