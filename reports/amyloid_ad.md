# Causal evidence appraisal — APP/amyloid → Alzheimer's disease

## 1. Verdict (BLUF)

**Headline tier: `likely_causal`** — the gated ordinal verdict.

- **Structural position:** `upstream_initiator`
- **Necessity × sufficiency:** `necessary_and_sufficient` — Monogenic-like: alone required and enough. Rare.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely causal, uncalibrated (prior 0.10 from base rate for a gene with prior monogenic evidence (curated set)) *(never exceeds the tier; digits shown only once calibrated)*

> Strong genetic causal support pairs with weak concurrent correlation, the signature of a node that acts early in the cascade and whose association to the measured outcome decays as causal distance grows. For illustration, amyloid in Alzheimer's disease -- bidirectional genetics, changes decades before symptoms, yet weak concurrent correlation with cognition.

**One-line:** upstream_initiator [necessary_and_sufficient] | scope: unscoped (no context specified -- verdict is not context-conditional) | tier: likely_causal | likely causal, uncalibrated (prior 0.10 from base rate for a gene with prior monogenic evidence (curated set))

> ⚠️ **Validation required.** 1 figure(s) RETRIEVED live this session from Open Targets Platform — tagged [RETRIEVED]; verify each in-source before use. 6 figure(s) from curated fixtures carry placeholder citations (TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use.

## 2. Causal question & estimand

Effect = M( system | do(X=a) ) − M( system | do(X=b) ), five slots filled:

- **X (intervened on):** APP/amyloid
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Causal DAG (adjustment set in words)

- **Exposure X:** APP/amyloid · **Outcome Y:** Alzheimer's disease
- **Instrument:** germline genotype (fixes direction; used by MR / genetic arms).
- **Adjustment set (back-door):** condition on shared common causes of X and Y (e.g. age, ancestry principal components); **do NOT** condition on downstream mediators or post-onset measurements.
- **Collider (do NOT adjust):** any selection node (survivorship in post-mortem cohorts, cell-line selection) — conditioning on it induces bias.

## 4. Four-explanation checklist

| # | Explanation | Design that addresses it | Status here |
|---|---|---|---|
| 1 | X → Y (causal) | MR + coloc; isogenic KI/rescue | supported |
| 2 | Y → X (reverse) | instrument fixed at conception; longitudinal | addressed (genotype fixed at conception) |
| 3 | Z → X, Z → Y (confound) | randomized / MR; conditional KO | addressed by genetic randomization |
| 4 | X → S ← Y (collider) | population sampling; IPW | modeled |

## 5. Evidence FOR

- [UNVERIFIED] **rare_penetrant_variant** (genetic, target_up_disease_up): no effect size on record [human/clinical_outcome]
    - ↳ source: `10.1038/349704a0` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **protective_allele** (genetic, target_down_disease_down): no effect size on record [human/clinical_outcome]
    - ↳ source: `10.1038/nature11283` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **cross_sectional** (association, target_up_disease_up): no effect size on record [human/disease_pathology]
    - ↳ source: `10.1212/WNL.0b013e31820af900` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - load-bearing assumption(s): no_selection_bias
- [UNVERIFIED] **anchored_onset_cohort** (temporal, target_up_disease_up): no effect size on record [human/biomarker]
    - ↳ source: `10.1056/NEJMoa1202753` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - load-bearing assumption(s): no_selection_bias
- [UNVERIFIED] **human_rct** (intervention, target_down_disease_down): no effect size on record [human/clinical_outcome]
    - ↳ source: `10.1056/NEJMoa2212948` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **biochemical_pathway** (mechanism, target_up_disease_up): no effect size on record [human/molecular_profile]
    - ↳ source: `10.15252/emmm.201606210` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 6. Evidence AGAINST / informative nulls

- [RETRIEVED] **observational_cohort** (association, null): 0.807 OT association score (0-1) (no CI)
    - ↳ source: Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession `opentargets_ENSG00000142192` — RETRIEVED live — integrated score, not a primary measurement; verify the underlying datatype evidence in-source before use.
    - Integrated backbone score only. Direction-less by construction; contributes to strength/consistency, never a causal tier. datatype scores: {'literature': 0.997, 'affected_pathway': 0.608, 'genetic_association': 0.866, 'clinical': 0.977}

## 7. Causal Strength Profile (CSP)

Identification gate: min(A1..A4) = **2** → gated tier **moderate** (controlled observation / single arm). Corroboration (B-axes) cannot lift this ceiling.

| Axis | Score (0–3) | Family |
|---|---|---|
| A1 Confounding Robustness | 3 | identification |
| A2 Reverse-Causation Robustness | 3 | identification |
| A3 Selection Robustness | 2 | identification |
| A4 Interventional Directness | 2 | identification |
| B1 Dose-Response Gradient | 0 | corroboration |
| B2 Temporal Precedence | 3 | corroboration |
| B3 Replication Breadth | 0 | corroboration |
| B4 Human Translatability | 3 | corroboration |

## 8. Evidence hierarchy (by dimension tier)

| Dimension | Tier | # items |
|---|---|---|
| association | weak | 2 |
| genetic | strong | 2 |
| intervention | moderate | 1 |
| mechanism | moderate | 1 |
| temporal | moderate | 1 |

## 9. Data & databases → named gaps

**Sources queried this appraisal:**

- **Hand-curated literature fixture** — C (paper-attached); retrieval: curated offline record. Cite: see per-item DOI/PMID (TODO:cite placeholders).
- **Open Targets Platform** — A (open, keyless); retrieval: live GraphQL query this session. Cite: Ochoa et al., Nucleic Acids Research 51:D1353 (2023) (doi:10.1093/nar/gkac1046).

**Named gaps:**

- No unexamined causal dimensions for this arrow.

## 10. Experimental roadmap

- **Next experiment (weakest, most cheaply strengthened):** A prevention-arm trial in mutation carriers (do(clear amyloid) BEFORE symptom onset). The modest late-intervention benefit is exactly what an early initiator predicts; the untested contrast is early intervention.

## 11. Conclusions


**Known limitations:**
- Effect depends on when you intervene; a static tier has no time axis.
- Driver and mediator are both causal; position is a relation, not a coordinate.
- Total and direct effects diverge; conditioning on a mediator can induce collider bias.
- Subgroup causality: a target causal only in a molecular subset needs (target, disease, subgroup) as the unit.

## 12. References

- [UNVERIFIED] `10.1038/349704a0` — 10.1038/349704a0 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1038/nature11283` — 10.1038/nature11283 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1212/WNL.0b013e31820af900` — 10.1212/WNL.0b013e31820af900 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [RETRIEVED] `10.1093/nar/gkac1046` — retrieved from Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession opentargets_ENSG00000142192, A (open, keyless)
- [UNVERIFIED] `10.1056/NEJMoa1202753` — 10.1056/NEJMoa1202753 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1056/NEJMoa2212948` — 10.1056/NEJMoa2212948 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.15252/emmm.201606210` — 10.15252/emmm.201606210 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
