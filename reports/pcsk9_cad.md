# Causal evidence appraisal — PCSK9 → coronary artery disease

## 1. Verdict (BLUF)

**Headline tier: `causal_driver`** — the gated ordinal verdict.

- **Structural position:** `validated_driver`
- **Necessity × sufficiency:** `necessary_and_sufficient` — Monogenic-like: alone required and enough. Rare.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely causal, uncalibrated (prior 0.05 from base rate for a randomly chosen gene-disease pair (curated set)) *(never exceeds the tier; digits shown only once calibrated)*

> Converging bidirectional causal evidence -- loss- and gain-of-function pointing opposite ways -- together with a successful human intervention place the target on the causal path with the strongest support the framework assigns. For illustration, PCSK9 in coronary disease -- loss-of-function alleles protect, gain-of-function causes familial hypercholesterolemia, and PCSK9 inhibitors cut events in outcome trials.

**One-line:** validated_driver [necessary_and_sufficient] | scope: unscoped (no context specified -- verdict is not context-conditional) | tier: causal_driver | likely causal, uncalibrated (prior 0.05 from base rate for a randomly chosen gene-disease pair (curated set))

> ⚠️ **Validation required.** 2 figure(s) RETRIEVED live this session from Open Targets Platform, gnomAD — tagged [RETRIEVED]; verify each in-source before use. 5 figure(s) from curated fixtures carry placeholder citations (TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use.

## 2. Causal question & estimand

Effect = M( system | do(X=a) ) − M( system | do(X=b) ), five slots filled:

- **X (intervened on):** PCSK9
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Causal DAG (adjustment set in words)

- **Exposure X:** PCSK9 · **Outcome Y:** coronary artery disease
- **Instrument:** germline genotype (fixes direction; used by MR / genetic arms).
- **Adjustment set (back-door):** condition on shared common causes of X and Y (e.g. age, ancestry principal components); **do NOT** condition on downstream mediators or post-onset measurements.
- **Collider (do NOT adjust):** any selection node (survivorship in post-mortem cohorts, cell-line selection) — conditioning on it induces bias.

## 4. Four-explanation checklist

| # | Explanation | Design that addresses it | Status here |
|---|---|---|---|
| 1 | X → Y (causal) | MR + coloc; isogenic KI/rescue | supported |
| 2 | Y → X (reverse) | instrument fixed at conception; longitudinal | addressed (genotype fixed at conception) |
| 3 | Z → X, Z → Y (confound) | randomized / MR; conditional KO | addressed by genetic randomization |
| 4 | X → S ← Y (collider) | population sampling; IPW | acknowledged, not fully modeled |

## 5. Evidence FOR

- [UNVERIFIED] **protective_allele** (genetic, target_down_disease_down): 0.12 OR (95% CI 0.03-0.45) [human/clinical_outcome]
    - ↳ source: `PMID:16554528` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - load-bearing assumption(s): no_horizontal_pleiotropy
- [UNVERIFIED] **rare_penetrant_variant** (genetic, target_up_disease_up): 2.8 OR (95% CI 1.9-4.1) [human/clinical_outcome]
    - ↳ source: `10.1038/ng1161` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **human_rct** (intervention, target_down_disease_down): 0.85 HR (95% CI 0.79-0.92) [human/clinical_outcome]
    - ↳ source: `PMID:28304224` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **human_rct** (intervention, target_down_disease_down): 0.85 HR (95% CI 0.78-0.93) [human/clinical_outcome]
    - ↳ source: `PMID:30403574` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **biochemical_pathway** (mechanism, target_up_disease_up): no effect size on record [human/molecular_profile]
    - ↳ source: `10.1074/jbc.M311730200` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 6. Evidence AGAINST / informative nulls

- [RETRIEVED] **biochemical_pathway** (mechanism, null): 1.144 LOEUF (no CI)
    - ↳ source: gnomAD (Karczewski et al., Nature 581:434 (2020); doi:10.1038/s41586-020-2308-7), accession `gnomad_constraint_PCSK9` — RETRIEVED live — constraint metric; confirm gene build/version and current gnomAD release before use.
    - gnomAD GRCh38 constraint: LOEUF=1.1441346736692857, pLI=2.765187110917745e-18. LOF-tolerant (unconstrained; haploinsufficiency less likely). Plausibility only -- cannot raise the causal tier (invariant #2).
- [RETRIEVED] **observational_cohort** (association, null): 0.718 OT association score (0-1) (no CI)
    - ↳ source: Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession `opentargets_ENSG00000169174` — RETRIEVED live — integrated score, not a primary measurement; verify the underlying datatype evidence in-source before use.
    - Integrated backbone score only. Direction-less by construction; contributes to strength/consistency, never a causal tier. datatype scores: {'literature': 0.964, 'genetic_association': 0.907, 'clinical': 0.933}

## 7. Causal Strength Profile (CSP)

Identification gate: min(A1..A4) = **2** → gated tier **moderate** (controlled observation / single arm). Corroboration (B-axes) cannot lift this ceiling.

| Axis | Score (0–3) | Family |
|---|---|---|
| A1 Confounding Robustness | 3 | identification |
| A2 Reverse-Causation Robustness | 3 | identification |
| A3 Selection Robustness | 2 | identification |
| A4 Interventional Directness | 2 | identification |
| B1 Dose-Response Gradient | 0 | corroboration |
| B2 Temporal Precedence | 0 | corroboration |
| B3 Replication Breadth | 0 | corroboration |
| B4 Human Translatability | 3 | corroboration |

## 8. Evidence hierarchy (by dimension tier)

| Dimension | Tier | # items |
|---|---|---|
| association | moderate | 1 |
| genetic | strong | 2 |
| intervention | strong | 2 |
| mechanism | moderate | 2 |

## 9. Data & databases → named gaps

**Sources queried this appraisal:**

- **Hand-curated literature fixture** — C (paper-attached); retrieval: curated offline record. Cite: see per-item DOI/PMID (TODO:cite placeholders).
- **gnomAD** — A (open, keyless); retrieval: live GraphQL query this session. Cite: Karczewski et al., Nature 581:434 (2020) (doi:10.1038/s41586-020-2308-7).
- **Open Targets Platform** — A (open, keyless); retrieval: live GraphQL query this session. Cite: Ochoa et al., Nucleic Acids Research 51:D1353 (2023) (doi:10.1093/nar/gkac1046).

**Named gaps:**

- No unexamined causal dimensions for this arrow.

## 10. Experimental roadmap

- **Next experiment (weakest, most cheaply strengthened):** None needed for causal status; bidirectional genetics and two positive outcome trials already converge. Remaining question is dose/timing optimization.

## 11. Conclusions


**Known limitations:**
- Effect depends on when you intervene; a static tier has no time axis.
- Driver and mediator are both causal; position is a relation, not a coordinate.
- Total and direct effects diverge; conditioning on a mediator can induce collider bias.
- Subgroup causality: a target causal only in a molecular subset needs (target, disease, subgroup) as the unit.

## 12. References

- [UNVERIFIED] `PMID:16554528` — PMID:16554528 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1038/ng1161` — 10.1038/ng1161 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `PMID:28304224` — PMID:28304224 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `PMID:30403574` — PMID:30403574 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1074/jbc.M311730200` — 10.1074/jbc.M311730200 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [RETRIEVED] `10.1038/s41586-020-2308-7` — retrieved from gnomAD (Karczewski et al., Nature 581:434 (2020); doi:10.1038/s41586-020-2308-7), accession gnomad_constraint_PCSK9, A (open, keyless)
- [RETRIEVED] `10.1093/nar/gkac1046` — retrieved from Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession opentargets_ENSG00000169174, A (open, keyless)
