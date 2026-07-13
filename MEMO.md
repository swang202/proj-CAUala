# How I'm building this — a memo

> 🧭 **Understand — motivation (best first read).** *Why* proj-CAUala exists and the problem it solves. Then read [README.md](README.md) (the *what*) and [CONCEPTS.md](CONCEPTS.md) (the *how* of the reasoning). Full map: **[docs/README.md](docs/README.md)**.

*Working notes on why proj-CAUala exists, what problem it solves, and the reasoning it has to get right. This is the "why"; the README is the "what," and the build brief is the "how."*

## The one-line reason this matters, and the gap

Causality is hard to hold onto. This tool exists to help us climb as close to it as the available evidence allows, and to be honest about how close that is. I think everyone doing biology should be asking this question before they commit, because the cost of mistaking association for causation is high:

- you don't want to chain two mechanisms together on a handful of experiments;
- you don't want to chase a target for ten years and a fortune only to find it was a passenger or bystander, not a driver;
- you don't want to give a patient a drug that can't help them because their disease isn't driven by that target.

Causality here is also conditional, not fixed. The same factor can be causal in one setting and irrelevant in another:

- gene A regulates B only in cell type C with characteristic D — not in every cell;
- a variant raises risk only on a particular genetic background or ancestry;
- a recognized early-onset-AD causal gene can be offset by a second, protective mutation.

So what we're after is not a yes/no label but a conditional claim — "A causes B *given this context*" — that shifts with genetic background, environment, cell state, and time. We still want to get as close to it as we can, because that conditional claim is what makes for better decisions about which biology to pursue.

**The gap I felt.** I sensed a hole between "figure out what's causal per factor" and "precision medicine," and it's this: a causal effect that's real on average in a population is not the same as a causal effect in one patient. You can never observe both outcomes in the same person, so individual causality is inferred, never measured, and can even point the opposite way from the population average. The tool does not jump that gap. It climbs a staircase — population → context-stratified subgroup → biomarker-defined microstratum → N-of-1 — trading statistical power for individual relevance at each step, with a mechanistic model doing the generalizing. Individual causality is the asymptote, not the deliverable. I'd rather name that plainly: what the tool promises is the best-supported *conditional* causal claim, with its context and uncertainty. That is a legitimate on-ramp to precision medicine, and it is not the same as saying "this is the driver, so treat this patient."

## Why the generic rules break in biology — the examples that convinced me

Part of why I want something built for biology rather than an off-the-shelf causal-inference algorithm is that, across my own experience studying disease, I keep running into real cases that break the standard rules outright. Every time a textbook criterion says "this is how you'd know it's causal," biology seems to hand me a counterexample. A few that stuck with me:

- **Dose–response isn't monotone.** The Bradford-Hill gradient assumes more exposure → more effect, but biology is full of U-shaped and hormetic curves — a factor protective at low levels and toxic at high ones, or the reverse. A monotone-gradient test would miss or misread these.
- **The same gene flips sign with context.** A variant that raises risk on one genetic background or ancestry can be neutral on another (antagonistic pleiotropy).
- **A bona fide causal gene can be silenced by a modifier.** A recognized, publicly accepted early-onset-AD mutation can be offset by a second protective variant, so a carrier never develops disease (the APOE Christchurch / resilience cases). A universal "gene → disease" claim breaks on epistasis.
- **Knockouts can mislead about necessity.** Delete a gene that genuinely matters and you can see nothing, because a paralog compensates (genetic robustness/redundancy). The naive reading "no phenotype ⇒ not causal" is backwards here.
- **Specificity runs both ways.** One cause → many phenotypes (pleiotropy), and many causes → one phenotype (the collection-of-diseases problem). Hill's specificity criterion barely survives contact with molecular biology.
- **Causality can be a loop, not an arrow.** Signaling and regulatory feedback mean A→B and B→A at the same time; an acyclic, single-direction assumption misses the real structure.
- **Thresholds and tipping points.** Nothing happens until a network crosses a tipping point and then collapses — the effect is invisible below threshold and abrupt above it, which no linear model catches.
- **Surprising cross-domain links.** Cancer-associated genes turning up in neurodegeneration, or the inverse comorbidity between some cancers and neurodegenerative disease — relationships I might have dismissed as "obviously just correlation" that turn out to have real biology underneath.

Each of these breaks a *different* rule of the standard commonality/association playbook, and that's the point: a tool that applies one fixed algorithm will be confidently wrong on exactly the cases that matter most. What I want is something that knows which rule it's allowed to trust for which kind of question — that adapts its evidence standard to the biology, instead of forcing the biology through a generic template. The design consequence is concrete: no single criterion is decisive on its own, the weighting is question-type-specific (see the evidence-stack registry), and the tool has to be able to *represent* non-monotone effects, sign flips, redundancy, feedback, and thresholds rather than assume them away.

## What I checked before starting

**1. How the field separates association from causation.** I surveyed how epidemiology defines and quantifies causal versus merely associated relationships, which criteria and algorithms exist (Bradford Hill; Pearl's ladder of association → intervention → counterfactuals; potential outcomes; Mendelian randomization; instrumental variables), and where the fine line sits. My read: these frameworks are the right foundation, but they were built for single-exposure epidemiology and need re-derivation for molecular biology (see README). In particular:

- **Specificity** mostly fails here — most "diseases" are *collections* of diseases with similar phenotypes but different underlying mechanisms. The useful reframe is *specificity of the perturbation* (on-target/off-target control), not one-cause-one-disease.
- This forces the **necessity vs. sufficiency** distinction to the center, and both directions of it matter, because a factor can sit in any of four boxes and the box decides what you do about it:
  - **Necessary *and* sufficient** — the factor alone both must be present and is enough. Classic monogenic disease; rare.
  - **Necessary but *not* sufficient** — the factor is required for the disease, but on its own it can't produce it; it needs co-conspirators. Amyloid-β in Alzheimer's is the textbook case: Aβ appears to be required for the cascade, yet clearing it is not enough — tau, ApoE genotype, neuroinflammation, age, and network vulnerability all have to line up. I think this is part of why anti-amyloid monotherapy has underwhelmed: it removed a *necessary component*, not a *sufficient* one. Philosophically this is an **INUS** factor — an Insufficient-but-Non-redundant part of an Unnecessary-but-Sufficient set — and it may be the most common structure in complex disease.
  - **Sufficient but *not* necessary** — the factor can drive the disease on its own, but some other E can too; it's one of several independent routes to the same phenotype (the "collection of diseases" case).
  - **Neither** — a modifier, passenger, or bystander.
- The two middle boxes look nearly identical in a naive correlation but have opposite therapeutic and evidentiary meaning, so the tool has to tell them apart:
  - A necessary-but-not-sufficient driver (amyloid) is still a legitimate, high-value *gatekeeper* target — but the evidence will show that perturbing it *shifts risk without abolishing disease*, and the honest verdict is "necessary component; expect to need combination or upstream intervention." Its signature is loss-of-function evidence: remove A and the phenotype is reduced but *not gone*.
  - A sufficient-but-not-necessary driver only helps the subgroup it actually drives; its signature is that A produces the phenotype in a naive background (gain-of-function) yet is *absent in many patients*, so the verdict is a *stratified* one — "driver for the A-defined subtype."
- Concretely, these map to different experiments and are scored on **separate axes**: loss-of-function / knockout probes necessity (does the phenotype fail to appear without A?); gain-of-function in a naive background probes sufficiency (does A alone produce it?). The tool should report *both* — and therefore a *set* of context-scoped drivers with attributable weight and an INUS-style verdict, rather than a single global "cause."

**2. How Claude approaches these questions, and where it falls short.** I fed in a range of causal questions — does gene A raise gene B's expression; does a mutation cause a disease; does a disease change a gene's expression; plus surprising real pairs (a cancer gene affecting neurodegeneration; a degeneration-risk gene with a protective effect). Across questions the approach was consistent and the data-gap notes were genuinely useful, but three weaknesses stood out:

- **Citations are the biggest liability.** It searches literature, but often the decisive thing — the raw DEG matrix, the Perturb-seq / CRISPR readout, the human genetic effect size — isn't in the text at all. The fix is to make evidence a structured record with provenance (accession, effect size, CI, sample size, context, and a primary-data-vs-review flag), not a sentence, and to prefer databases over abstracts.
- **Directionality is under-used, and can't come from where it's easiest.** Cross-sectional co-expression carries essentially zero directional information. Direction has to come from genetics (genotype is fixed at conception, so the arrow points away from it — MR), from time-course/dosage series, or from perturbation. The ideal evidence is paired data across time or dose, so we can see whether A is upstream of B and whether the effect holds across contexts — that's two Bradford-Hill rungs (temporality + gradient) at once.
- **Scoring is impressionistic.** It needs to be defined: per question type, a fixed rubric with 0–3 anchors, *separate* axes for evidence-for and evidence-against/confounded, effect sizes normalized within modality, an explicit base-rate prior (most gene–disease pairs are null), and a calibrated posterior — surfaced as a spider chart plus one confidence number. And it has to say what data it most urgently needs, and how much is enough to stop.

## The future — an ideal scenario

Biology is a high-dimensional network, and causality is a matter of finding a path through it that holds when you pull on it.

I'll start simple: one question at a time, A → B in a stated context. But the aim is a small step toward precision medicine. In the ideal, for an individual with a given genetic background and epigenetic state, we could probe and identify the driver of *their* disease, and from that choose a drug that actually helps that patient or that stratified population. This tool is the first rung: turning "A is associated with B" into "A causes B, in context C, to this degree, with this confidence — and here's the experiment that would prove me wrong."
