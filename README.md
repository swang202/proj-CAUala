# proj-CAUala 🐨

**proj-CAUala: Climbing the causal tree.** Turn "A is associated with B" into "A causes B, *in context C*, to this degree, with this confidence — and here is the experiment that would settle it."

CAUala takes a biological causal question, figures out *which arrow* is being asked about, pulls only the evidence types that can actually establish that arrow, scores them through a biology-adapted causal framework on separate for/against axes, hunts the confounder specific to each data type, updates a base-rate prior into a calibrated posterior, and returns a **conditional** driver / passenger / bystander verdict with a falsifiable roadmap.

> **Design principle #1 — conditional, not global.** The atomic claim is `A → B | context`, never a context-free "A causes B." Verdicts are scoped to the context (cell type, tissue, background/ancestry, sex, disease subtype, stage, dose, time) in which the evidence exists; generalization beyond that is flagged, not assumed.
>
> **Design principle #2 — a mechanism story can never raise a causal score.** Plausibility is a tiebreaker only. Evidence is structured records with provenance, not sentences.
>
> **Design principle #3 — population ≠ individual.** CAUala reports population/subgroup-conditional causality and treats individual causality as the asymptote it climbs toward by finer conditioning. It never claims an individual verdict it can't support.

---

## The Causal Tree (Bradford Hill + Pearl, re-derived for molecular biology)

**Pearl's ladder** sets the frame: Association (seeing) → Intervention (doing, *do*(X)) → Counterfactuals (imagining). CAUala's job is to move a claim **up** the ladder — from co-occurrence toward interventional and counterfactual support — and to score how far up the evidence actually reaches.

**Bradford Hill's nine considerations, adapted.** Not a checklist to tally — viewpoints, weighted by how well each isolates the do-operator:

| Criterion | Transfers to biology? | How CAUala uses it |
|---|---|---|
| **Strength** (effect size) | ✅ Yes | Normalized within modality (z/rank) so effects are comparable across data types. |
| **Consistency** (reproducibility) | ⚠️ Context-dependent | Scored **within directional evidence only**; "reproduced in same context" and "generalizes across contexts" are *separate* axes. |
| **Temporality** | ✅ Yes — essential | The one necessity. Longitudinal / time-course; genotype-fixed direction. No temporality ⇒ no directional credit. |
| **Biological gradient** (dose–response) | ✅ Yes | Dose/titration series (CRISPRa/i, compound curves); a monotone gradient is hard to fake. |
| **Coherence** | ✅ Yes | Agreement across genetic, molecular, and clinical layers. |
| **Experiment** | ✅ Yes — top tier | Perturbation = the do-operator made physical. Highest causal weight. |
| **Reversibility** | ✅ **Promote to top tier** | Knock down → phenotype goes; rescue → it returns. Re-runs the causal contrast in one system. |
| **Specificity** | ❌ Reframe | Kill "one cause → one disease" (most disease is a *collection*). Keep only as **perturbation specificity** — an on/off-target data-quality gate. |
| **Plausibility** | ⚠️ Tiebreaker only | A mechanism story must never raise a score on its own — it's how false claims feel true. |
| **Analogy** | ❌ ~Zero weight | Rhetorical. Kept only as a hypothesis-generation note. |

**Necessity vs. sufficiency** sits at the center, because most disease is polygenic/heterogeneous. Loss-of-function evidence speaks to **necessity** (does Y fail without X?); gain-of-function in a naive background speaks to **sufficiency** (does X alone produce Y?). A factor can be one without the other, so CAUala reports a **set** of context-scoped drivers with attributable weight — not a single cause.

**Causal tiers (evidence weighting, strongest → weakest):**
1. Randomized human intervention (RCT) · isogenic CRISPR knock-in **+ rescue**
2. Mendelian randomization (concordant, pleiotropy-tested) · dose-response perturbation (CRISPRa/i titration) · reversibility/rescue
3. Single perturbation without rescue (CRISPR KO, Perturb-seq, L1000) · colocalized eQTL–GWAS
4. Longitudinal / temporal-ordered observational · fine-mapped genetic association
5. Cross-sectional association, co-expression, DEG lists → **hypothesis only; zero directional credit**

---

## What the tool does

### 1. Type the question → know which arrow is asked
Parse the question into `source → target | context`, where each node is typed (variant · gene-expression · protein-level/activity · pathway/module · cell-state · phenotype/disease · drug) and the edge is typed (regulatory · physical · genetic-risk · causal-effect), with **direction** and **context** slots. Combinations (gene→gene, variant→disease, disease→gene, drug→phenotype, …) each route to a different evidence stack. *This ontology is the spine of the tool.*

### 2. Know what evidence is needed — and query real data, not just text
For each question type, a **canonical evidence stack** lists the study designs and databases that can establish *that* arrow, ranked by causal tier. CAUala queries structured databases across:

- **human genetics / natural experiments:** GWAS, Mendelian randomization, eQTL colocalization, gnomAD constraint, ClinVar/OMIM/ClinGen curation;
- **perturbation / the do-operator:** DepMap CRISPR KO, LINCS L1000, Perturb-seq / CRISPRi/a (scPerturb), drug/chemical perturbation;
- **context / expression:** single-cell atlases (CELLxGENE), transcriptomic/proteomic/epigenomic/ATAC-seq, GEO;
- **integrated evidence + literature:** Open Targets (backbone), Europe PMC text-mined relations.

Across model systems (human, iPSC, animal, primary, immortalized lines) and timescales (cross-sectional, longitudinal, dose). Every evidence item is a **structured record**: accession/DOI, effect size + CI, sample size, context, assay, directionality flag, and primary-data-vs-review-vs-text-mined provenance — with a **retraction/replication check**.

> **Build on Open Targets, don't reinvent it.** Open Targets already integrates genetics (L2G, fine-mapping, colocalization — Genetics merged into the Platform in 2025), expression, and perturbation into a target–disease score. Use it as the v1 backbone and benchmark; CAUala's differentiator is the **causal re-scoring** on top: directionality tagging, the do-operator tier, reversibility, conditional/context verdicts, and calibrated posteriors.

### 3. Weigh directionality and agreement — don't average
Track how many datasets exist, whether they **agree in direction**, and where they conflict. Aggregate with **tier-weighted, direction-aware Bayesian updating**, not naive averaging. **Conflict is a first-class output** ("genetics says up, L1000 says down — likely because…"), never smoothed away. Attend to dose and time effects explicitly.

### 4. Know when to stop — value-of-information, not vibes
Stop when (a) top-tier evidence is already conclusive, **or** (b) the best remaining unqueried evidence type can't change the verdict (marginal VOI below threshold), **or** (c) the question type's evidence checklist is filled. Always report **why it stopped and what it didn't look at.** Never silently truncate.

### 5. Return a decision object
For each question, in the driver / passenger / bystander frame — **scoped to context**:

- a short **verdict** with a **spider chart** over the adapted criteria (the full vector) **and** a single calibrated posterior;
- **evidence for** and **evidence against**, with an explicit **confounder hunt keyed to the data type** (LD, population stratification, pleiotropy, batch, cell-type composition, collider/selection, reverse causation);
- a **correlation-vs-causation summary table**;
- an **evidence hierarchy** ranked by causal weight;
- a **database compendium** with source records / citations (structured, provenance-bearing);
- an **experimental roadmap** to prove/disprove — the "what would change my mind" test (Anatomy toolkit: MR as the instrumental-variable play, isogenic CRISPR knock-in + rescue, CRISPRa/i dose-response, reversibility, mediation analysis);
- a **"where the field stands" causal map**, and a flag if the disease label is **too coarse** (maps to many subtypes) and should be stratified.

---

## Validation (do this first)
Verdicts are only trustworthy if calibrated. Build the harness before trusting output: a **gold-standard positive set** (ClinGen "Definitive/Strong," OMIM monogenic), a **negative/hard set** (curated non-associations; retracted/failed-replication claims), calibration by confidence bin, and an external anchor (genetically-supported drug targets succeed ~2× more often — the tool should reproduce that separation).

## Status
Design phase. See `CAUala-critique.md` (the reasoning stress-test), `memo.md` (the why), and `CAUala-build-brief.md` (the engineering handoff, with schemas and connector stubs).
