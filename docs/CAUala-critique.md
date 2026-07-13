# proj-CAUala — Critique: Loopholes in the Logic and the Process

> 🧭 **Understand — the reasoning stress-test.** The loopholes in the logic, found and closed before any code. Context: [MEMO.md](../MEMO.md) and [CONCEPTS.md](../CONCEPTS.md). Docs map: **[docs index](README.md)**.

*A stress-test of the memo + README against the causal-inference framework, before you hand anything to an engineer. Read this first; the file rewrites and the build brief act on everything here.*

The core instinct is right, and it is unusually well-posed: **most biology quietly reports association and narrates it as causation, and the cost of that error is measured in decades and fortunes and mistreated patients.** A tool that forces every "A causes B" claim to declare which evidence actually pins down *do*(A) — and which is just co-occurrence dressed in a mechanism story — is worth building. What follows is not disagreement; it is the set of places where the current logic will leak if it isn't tightened before code is written.

---

## Part 1 — Loopholes in the logic

### L1. A single verdict contradicts your own "fluid matrix"
Your memo's sharpest insight is that causality here is *conditional* — gene A drives B only in cell type C, only on genetic background D, only at a disease stage. But the README then asks for **one** driver/passenger/bystander verdict with **one** spider chart per question. Those two ideas are in tension. If the output is a single context-free label, the tool reproduces exactly the over-simplification you're trying to kill.

**Fix:** the atomic unit of output is not "A → B" but **"A → B | context"**. Formally this is a *conditional average causal effect* (effect modification). The verdict object must carry a context vector (cell type, tissue, background/ancestry, sex, disease subtype, developmental stage, dose, time) and the tool should return a **small set of context-stratified verdicts**, not one. Where evidence exists in only one context, the verdict is explicitly scoped to that context and the generalization is flagged as untested — not assumed.

### L2. The precision-medicine "gap" you flagged is real, and it has a name
You wrote that you feel a gap between "define what's causal per factor" and "precision medicine," and asked me to find it. Here it is: **a causal effect that is real *on average in a population* is not the same as a causal effect *in one patient*.** This is the fundamental problem of causal inference — you can never observe both potential outcomes in the same individual, so individual causality is never measured directly, only inferred. Population-average and even subgroup-average effects can point the opposite way from a given person's (Simpson's paradox is the population-scale version of this).

**The bridge (this is the missing logic to convey):** the tool doesn't leap from population to individual. It *climbs a staircase of conditioning* — population → context-stratified subgroup → biomarker-defined microstratum → N-of-1 — and each step trades statistical power for individual relevance. Individual-level causality is the **asymptote**, approached from two directions at once: (a) ever-finer stratification of interventional evidence, and (b) a **mechanistic model** general enough to instantiate for one person's genotype/epigenome. Say this explicitly. The tool's honest promise is "the best-supported *conditional* causal claim given everything known, with its context and its uncertainty" — that is the legitimate on-ramp to precision medicine, and it's defensible. The illegitimate version ("this gene is the driver, therefore treat this patient") is the gap, and naming it is what makes the project credible rather than hand-wavy.

### L3. Direction cannot come from the data type you lean on most
The memo leans on DEG / co-expression data ("gene A measured with gene B across individuals"). But **cross-sectional co-expression carries essentially zero directional information** — it can't tell A→B from B→A from Z→both. If the scorer awards causal credit for co-expression, it will systematically launder association into causation, which is the whole failure mode you're attacking.

**Fix:** tag every evidence item with a **directionality capability** flag. Direction can come from: genetics as a natural experiment (MR / genotype is fixed at conception, so the arrow can only point away from it), temporal ordering (longitudinal, pseudotime with heavy caveats), or perturbation (the do-operator gives direction natively). Cross-sectional correlation contributes to *strength/consistency* at most, and **never** to *direction*. Make this a hard rule in the scoring engine, not a footnote.

### L4. Bradford Hill was built for single-exposure epidemiology — four of its rungs mis-transfer to molecular biology
Your README already senses this; here is the precise re-derivation the user (and the tool) needs:

- **Specificity** — you're right it's weak. But don't just weaken it; **reframe** it. In molecular causality the useful form of "specificity" is *specificity of the perturbation* (did the CRISPR guide hit only the intended gene? is there an off-target/rescue control?), not *specificity of cause→disease*. One-cause-one-disease is false for essentially all common disease (your "collection of diseases" point). So: kill disease-specificity as a criterion, add perturbation-specificity as a data-quality gate.
- **Reversibility** — you filed this under "be cautious," but in biology it is one of the **strongest** available tests: knock the factor down, phenotype goes; restore it, phenotype returns (rescue). That's re-running the causal contrast inside one system. It should be **promoted to a top tier**, not treated with suspicion.
- **Plausibility** — this is the dangerous one. A plausible mechanism story is *the exact thing that makes a false causal claim feel true* (it's how good scientists get fooled, and it's what an LLM is best at manufacturing). Plausibility must be a **tiebreaker only**, never primary evidence, and the tool should be architected so that a mechanism narrative can *never* raise a causal score on its own.
- **Analogy** — near-purely rhetorical; assign it ~zero causal weight (keep it only as a hypothesis-generation note).

### L5. "Consistency" hides a context confound
"Gene X is consistently up in disease across ten datasets" feels like strong evidence and is often just **consistent association** — ten datasets can share the same confounder (all cross-sectional, all the same reverse-causation trap). And per L1, consistency *across* contexts and consistency *within one* context mean different things. Conflating them inflates confidence.

**Fix:** score consistency **within directional evidence only**, and separate "reproduced in the same context" from "generalizes across contexts" — they populate different axes of the verdict.

### L6. The confounder hunt is generic where it must be data-type-specific
The README says "hunt confounders" but a generic hunt finds nothing. Each data modality has a **signature confounder** the tool must check for by name:

- **GWAS / genetics:** linkage disequilibrium (the variant you see merely *tags* the causal one — the genomic confounder par excellence), population stratification, winner's curse.
- **Mendelian randomization:** horizontal pleiotropy (the instrument affects the outcome through a second path) — this *breaks* MR and must be tested (MR-Egger, weighted median, outlier tests).
- **Bulk omics:** cell-type composition shifts masquerading as expression changes; batch effects.
- **Patient cohorts / case-only designs:** collider/selection and survivorship bias; ascertainment.
- **Any observational omics:** reverse causation (the disease state changing the gene, not vice versa).

**Fix:** the confounder module is a **lookup keyed to data type**, each with a specific test and a specific down-weight when the test can't be run.

### L7. You cannot average your way to an unbiased answer
The README asks to "normalize it to get an unbiased result." Naive averaging across evidence types is itself a bias: a genome-wide-significant MR result and a single cross-sectional correlation are not two votes of equal weight, and **conflicting directions should be surfaced, not smoothed away** (a genetics-vs-perturbation disagreement is often the most informative thing in the whole report). 

**Fix:** aggregate with **tier-weighted, direction-aware Bayesian updating**, and treat conflict as a first-class output ("genetics says up, L1000 says down — here's the likely reason"). Averaging destroys exactly the signal you want.

### L8. Without a prior, the tool will over-call causality
Base rate matters: for a random gene–disease pair the prior probability of a true causal relationship is **low**. A "moderate" evidence score against a low prior still means *probably not causal* — but a tool that reports evidence scores without a prior will read moderate evidence as a positive verdict and systematically over-call. This is the single most likely way the tool embarrasses itself.

**Fix:** make the output an explicitly **Bayesian posterior** (prior × likelihood-from-evidence), report the prior you used and where it came from (e.g., pair is/ isn't in a curated set, gene constraint, network distance), and calibrate so that "high confidence" actually corresponds to a high hit rate on a held-out gold standard (see P5).

---

## Part 2 — Loopholes in the process / workflow

### P1. "What evidence is needed" requires a question ontology, not a text search
The tool's whole value hinges on knowing, *for this specific question type*, which experiments could settle it. That requires a **controlled ontology**: node types (variant, gene-expression, protein-level/activity, pathway/module, cell-state, phenotype/disease, drug) × edge types (regulatory, physical, genetic-risk, causal-effect) × direction × context. Each (node-pair, edge-type) maps to a **canonical evidence stack** — the ranked list of study designs and databases that can establish *that* arrow. This lookup table is the heart of the tool; without it, "what's needed" defaults to keyword search, which is the current failure mode.

### P2. Citations must become records, not sentences
You correctly named citations as the biggest liability. The deeper fix: **evidence is a structured record with provenance** — accession/DOI, effect size + CI, sample size, context, assay, and a flag for *primary data vs. review assertion vs. text-mined mention*. A claim with no queryable record behind it cannot raise a score. Add a **retraction/reproducibility check** (a retracted or failed-to-replicate source is worse than no source). This also defends against the LLM-summarization failure mode where an abstract's optimistic phrasing becomes "evidence."

### P3. "Stop when it's enough" needs a stopping rule, not a feeling
You asked for the matrix. Use **value-of-information**: stop when (a) top-tier evidence is already conclusive (e.g., isogenic knock-in + rescue *and* concordant MR), **or** (b) the best remaining unqueried evidence type *cannot change the verdict* given what's already in hand (marginal VOI below threshold), **or** (c) the pre-registered evidence checklist for that question type is filled. Report *why* it stopped and *what it didn't look at*. Never silently truncate — a skipped modality that would have disagreed is exactly what you need to see.

### P4. The scoring rubric has to be written down before it can be trusted
"Impressionistic" is the right self-diagnosis. Define, per criterion, a **0–3 anchor scale** with explicit word-pictures for each level; keep **two separate axes** (evidence *for* and evidence *against/confounded*, never netted into one number until the end); **normalize effect sizes** within modality (z-score or rank, so a big L1000 effect and a big MR effect are comparable); and weight each criterion by the **causal tier** of the data behind it. Emit the full vector (that's your spider chart) *and* a single calibrated posterior. The vector preserves nuance; the posterior forces a decision.

### P5. There is no validation plan — this is the biggest process gap
Nothing in the drafts says how you'll know the verdicts are *right*. Without that, the tool is unfalsifiable and no one should trust it. You need:

- A **gold-standard positive set** (ClinGen gene–disease validity "Definitive/Strong"; OMIM monogenic pairs) and a **negative/hard set** (curated non-associations, and retracted or failed-replication claims).
- **Calibration**: bin verdicts by stated confidence and check the hit rate matches (a "90% confident" bin should be right ~90% of the time).
- An **external anchor**: genetically-supported drug targets succeed in the clinic at roughly twice the base rate — a well-calibrated tool should reproduce that separation on target–disease pairs. Use it as a sanity check.

Build the gold-standard harness *first*; it's what turns the scoring rubric from opinion into something measurable.

### P6. Identifier and ontology harmonization is a silent prerequisite
Every database uses different IDs. Without a normalization layer the joins simply fail and the tool quietly under-reports evidence (looks like "no evidence," is actually "no join"). Standardize on: **Ensembl/HGNC** for genes, **variants** on GRCh38 with rsID↔HGVS mapping, **MONDO/EFO** for disease, **HPO** for phenotype, **ChEBI/CHEMBL** for compounds, **Uberon/CL** for tissue/cell type. The "collection of diseases" problem lives here too: the tool must **detect when a disease label is too coarse** (maps to many MONDO subtypes) and either stratify or warn.

### P7. Don't reinvent Open Targets — stand on it
Much of what the README describes (integrating genetics, expression, perturbation, and literature into a target–disease evidence score) is **already** what Open Targets does, and as of mid-2025 it absorbed Open Targets Genetics (L2G, fine-mapping, colocalization) into one GraphQL API. Two implications: (1) Open Targets is the fastest possible **backbone** for v1 — don't hand-roll GWAS→gene assignment; query theirs. (2) It's also your **benchmark and your differentiator**: Open Targets gives an association-weighted evidence score; *your* contribution is the explicit association-vs-causation epistemics — directionality tagging, the do-operator tier, reversibility, conditional/context verdicts, and calibrated posteriors. Position the tool as "Open Targets' evidence, re-scored through a causal lens," not "Open Targets from scratch."

---

## Part 3 — Priority order (what to fix before writing code)

1. **Adopt the conditional estimand** (L1/L2): the output unit is "A → B | context," and population-vs-individual is stated honestly. Everything else depends on this.
2. **Build the question ontology → canonical evidence stack** (P1). This is the tool's spine.
3. **Make evidence a structured, provenance-bearing record with a directionality flag** (P2/L3).
4. **Write the scoring rubric with for/against axes, tier weights, and a Bayesian prior** (P4/L7/L8).
5. **Stand up the gold-standard validation harness before trusting any verdict** (P5).
6. **Key the confounder hunt to data type** (L6), and **re-derive the four mis-transferring Hill criteria** (L4/L5).
7. **Use Open Targets as backbone + benchmark** (P7); layer the causal re-scoring on top.

---

## One-paragraph summary you can paste into the memo

*The tool's job is not to declare "A causes B." It is to return the best-supported **conditional** causal claim — "A causes B in context C, to this degree, with this confidence" — by (1) typing the question, (2) pulling only the evidence types that can actually establish that arrow, (3) scoring each on separate for/against axes weighted by how well its design isolates the do-operator, (4) hunting the confounder specific to each data type, (5) updating a base-rate prior into a calibrated posterior, and (6) handing back a falsifiable experimental roadmap for what would settle it. Population-average causality is where it lives today; individual causality is the asymptote it climbs toward by conditioning ever more finely — and that staircase, stated honestly, is the real on-ramp to precision medicine.*
