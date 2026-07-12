# Causal Evidence Report — Specification & Scoring Rubric

*House style for the causal-evidence review tool. Every report is generated to this template so outputs are consistent, auditable, and comparable across genes/diseases. Built from the v2 report set (the MS4A6A report is the reference bar).*

---

## 0. Global rules (apply to every report)

**Provenance tags** — every quantitative claim (OR, r, p, n, fold-change, %) carries exactly one:

- `[VERIFIED]` — title/venue/identifier confirmed against a primary source retrieved this session; cite DOI/PMID.
- `[RETRIEVED]` — a URL was retrieved this session (metadata seen), full text not read; the number must still be verified in-source before use.
- `[TRAINING — verify]` — from model knowledge, not confirmed against a document. Never present as a checked fact.
- `[INFERRED]` — logically follows from tagged premises; not independently observed.

**Confidence tiers** — every *conclusion* is one of:

- `ESTABLISHED` — supported by ≥2 independent experimental systems with appropriate controls.
- `INFERRED` — holds only under a stated, named assumption (with sensitivity note).
- `SPECULATIVE` — plausible, not yet tested.

**Hard rules**

1. No quantitative figure is stated without a provenance tag. Unverifiable numbers are ranged or omitted, never asserted.
2. Every causal claim carries a **load-bearing assumption** + a one-line **sensitivity note** ("conclusion flips if …").
3. Every association is run through the **four-explanation checklist** before any causal language.
4. Bradford Hill is used as *viewpoints, not a tally* — never "satisfies 8 of 9."
5. **Always prefer raw data and validate.** When a claim can be checked against a public dataset, say which dataset, whether raw or processed, and what recomputation would confirm it (see companion Data-Source Catalog).
6. Report the **Causal Strength Profile** (Section 7) for the headline claim, scored on the anchored rubric.

---

## 1. Canonical section order

| # | Section | Purpose |
|---|---|---|
| 1 | **Verdict (BLUF)** | One paragraph + confidence tier. What is/ isn't established. |
| 2 | **Causal question & estimand** | The formal `do()` contrast, filled slots (below). |
| 3 | **Causal DAG** | Graph + node roles + **adjustment set** + explicit assumptions. |
| 4 | **Four-explanation checklist** | X→Y, Y→X, common-cause Z, collider — for the key association. |
| 5 | **Evidence FOR** | Each item: provenance + confidence + assumption + sensitivity + axis scores. |
| 6 | **Evidence AGAINST / negatives** | Including informative null results. |
| 7 | **Causal Strength Profile** | Spider chart + scoring table (Section 3 of this spec). |
| 8 | **Evidence hierarchy** | Every method scored on the *one* unified rubric. |
| 9 | **Data & databases → named gaps** | Each source tied to a gap, with access class + query. |
| 10 | **Experimental roadmap** | Each step → DAG path it addresses + axis it moves + assumption. |
| 11 | **Conclusions by confidence tier** | ESTABLISHED / INFERRED / SPECULATIVE, separated. |
| 12 | **References** | `[verified]` / `[unverified]` per entry, with DOI/PMID. |

---

## 2. The estimand (Section 2 must fill all five slots)

Every report states the causal question as an interventional contrast, not a correlation:

> **Effect = M( system | do(X = a) ) − M( system | do(X = b) )**

| Slot | Definition | Must be explicit |
|---|---|---|
| **X** | the thing intervened on | gene, variant, activity state |
| **a vs b** | the two contrasted levels | KO vs WT; risk vs ref allele; dose 0 vs 1 |
| **M** | the readout scored | *specify total-protein vs PTM vs phenotype* — the APP-tau lesson: define M precisely or the question is ambiguous |
| **system** | context held fixed | cell type, background, stage |
| **population** | over whom the average is taken | e.g. European-ancestry, onset < 65 |

If X, a/b, or M is ambiguous, **split the question** (as APP-tau split "tau overexpression" into total-tau vs pTau) and score each separately.

---

## 3. The DAG (Section 3 requirements)

Non-negotiable elements:

1. Nodes typed and visually distinct: **exposure X**, **outcome Y**, **mediator(s) M**, **confounder(s) Z/U**, **collider(s) S**, **instrument (genotype)**.
2. Solid = established edge; dashed = inferred/partial; gold "?" = disputed arrow.
3. **The adjustment set stated in words** — the payoff of drawing the DAG. e.g. *"To estimate X→Y by the back-door criterion, condition on {age, APOE4}; do NOT condition on {plaques, postmortem cohort} (mediator / collider)."*
4. A numbered **list of assumptions** the graph encodes (each an arrow present or absent), so they can be argued with.
5. The collider is always drawn and labeled **"do NOT adjust."**

---

## 4. Four-explanation checklist (Section 4)

A fixed table applied to the headline association. Every row must be filled — collider is the one most often skipped and must never be blank.

| # | Explanation | Concrete instance | Design that addresses it | Status |
|---|---|---|---|---|
| 1 | X → Y (causal) | … | MR + coloc; isogenic KI/rescue | … |
| 2 | Y → X (reverse) | … | instrument fixed at conception; longitudinal | … |
| 3 | Z → X, Z → Y (confound) | … | randomized/MR; conditional KO; PCA/LMM | … |
| 4 | X → S ← Y (collider/selection) | survivorship in postmortem; iPSC-line selection | population sampling; IPW; model selection | … |

---

## 5. The unified scoring rubric — Causal Strength Profile (CSP)

This replaces the ad-hoc star ladders (which differed in every v1 report). **One rubric, eight axes, each scored 0–3 with fixed anchors.** Plotted as a spider/radar chart per claim.

### The eight axes

Grouped into two families. Family A ("did we rule out the rival explanations?") is the *identification* half; Family B ("how strong is the positive signal?") is the *corroboration* half.

**Naming principle:** each axis names the *capability being scored*, phrased so that **higher always means stronger causal evidence** — never the bare threat (e.g. "Confounding Robustness," not "confounding," which reads backwards). The three Family-A bias axes share the word **"Robustness"** = robust to that failure mode.

**Family A — Identification (rules out the four rival explanations)**

| # | Axis | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|
| A1 | **Confounding Robustness** (robust to common-cause Z) | none | adjust measured covariates | design limits it (isogenic / conditional) | eliminated by design (RCT / MR / randomized allele) |
| A2 | **Reverse-Causation Robustness** (robust to Y→X) | none | temporal ordering only | manipulation in a model system | instrument fixed *before* outcome (genotype / randomization) |
| A3 | **Selection Robustness** (robust to collider / selection bias) | unexamined | acknowledged | partially modeled | population sampling or IPW; selection modeled explicitly |
| A4 | **Interventional Directness** (rung of Pearl's ladder reached) | pure observation | associational + covariates | one-shot perturbation `do(X)` | **reversible** in-system `do(X)` (degron/optogenetic on-off) |

**Family B — Corroboration (Bradford Hill signal strength)**

| # | Axis | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|
| B1 | **Dose–Response Gradient** | none | two-point (KO vs WT) | ordinal series | monotone graded titration (allelic series / CRISPRa-i curve) |
| B2 | **Temporal Precedence** (cause observed to precede effect) | unknown | cross-sectional guess | ordering in a model | precedence shown in longitudinal human data |
| B3 | **Replication Breadth** | single study | 2 studies, one system | multiple independent labs | independent across systems *and* ancestries/models |
| B4 | **Human Translatability** | in silico / non-mammalian | mouse model | human cells / tissue | human population or in-vivo human genetics |

Max = 24. Plot the eight scores on a radar; the **shape** is the message, not just the area.

*Note A2 vs B2:* A2 (Reverse-Causation Robustness) is **structural** — the cause is fixed before the outcome by design (a germline allele). B2 (Temporal Precedence) is **observational** — the ordering was actually seen in longitudinal data. Different axes; keep them distinct.

### The identification gate (critical rule)

A high corroboration score cannot rescue weak identification — the epistemics point that *precision ≠ identification*. Enforce a ceiling:

> **Overall causal tier ≤ min(A1, A2, A3, A4) mapped to tiers.**
> A claim with A1=0 (no confounding control) is capped at "association," no matter how large B1–B4 are.

Report both: the **profile** (all 8 axes, shows *where* the gap is) and the **gated tier** (the honest ceiling). Two claims can have the same area and very different gated tiers — that is the point.

### Per-method vs per-claim

- **Per-method:** score each individual study/method on the 8 axes (a bench cell-culture study might be A1=2, A4=2, B4=1 …). Feeds Section 8's hierarchy.
- **Per-claim CSP (the spider chart):** for each axis, take the **best score any supporting study achieves on that axis**, then apply the identification gate. This shows "the strongest available identification per dimension" and exposes the axis that is holding the claim back.

### Tier mapping (for the gate and the verdict)

| Gated tier | Meaning | Requires (min of A1–A4) |
|---|---|---|
| **5 Definitive** | interventional proof in relevant system | ≥3 on the binding axis + replication |
| **4 Strong** | quasi-experimental, one major assumption open | 3 |
| **3 Moderate** | controlled observation / single arm | 2 |
| **2 Suggestive** | association + mechanism | 1 |
| **1 Association** | correlation only | 0 |

---

## 6. Sections 9–11 rules

- **Databases (Section 9):** no generic compendium. Each entry = `named gap → source → access class → exact query → raw or processed`. Access class from the Data-Source Catalog (A open / B controlled / C paper-attached).
- **Roadmap (Section 10):** each step names (a) the DAG path it tests, (b) which CSP axis it raises, (c) the load-bearing assumption, (d) the specific dataset/design.
- **Conclusions (Section 11):** grouped under ESTABLISHED / INFERRED / SPECULATIVE. The headline verdict never exceeds the gated tier from Section 7.

---

## 7. Definition of "done" (tool self-check before emitting)

- [ ] Estimand fills all five slots; M is unambiguous (or the question was split).
- [ ] DAG present with typed nodes, adjustment set in words, assumption list, labeled collider.
- [ ] Four-explanation table has no blank rows (collider filled).
- [ ] Every quantitative claim has a provenance tag; no untagged numbers.
- [ ] Every causal claim has assumption + sensitivity note.
- [ ] CSP scored on all 8 axes; identification gate applied; verdict ≤ gated tier.
- [ ] Databases tied to named gaps with access class + raw/processed noted.
- [ ] References carry [verified]/[unverified]; ≥1 live-verified for any headline number.
- [ ] Bradford Hill used as viewpoints, not tallied.
