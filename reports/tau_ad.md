# Causal evidence appraisal — tau → Alzheimer's disease

## 1. Verdict (BLUF)

**Headline tier: `plausible`** — the gated ordinal verdict.

- **Structural position:** `downstream_mediator`
- **Necessity × sufficiency:** `undetermined` — Necessity/sufficiency not established; loss- and gain-of-function needed.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely non-causal, uncalibrated (prior 0.10 from base rate for a strong biomarker with weak disease-specific genetics (curated set)) *(never exceeds the tier; digits shown only once calibrated)*

> Strong association and a plausible mediating position combine with weak independent genetic support: an excellent biomarker but an uncertain target, because a mediator IS causal yet its position in the graph is a relation, not proof of primacy. For illustration, tau in Alzheimer's disease -- it tracks cognitive decline better than amyloid because it sits closer to the effector end of the chain, not because it is more causal.

**One-line:** downstream_mediator [undetermined] | scope: unscoped (no context specified -- verdict is not context-conditional) | tier: plausible | likely non-causal, uncalibrated (prior 0.10 from base rate for a strong biomarker with weak disease-specific genetics (curated set))

> ⚠️ **Validation required.** 1 figure(s) RETRIEVED live this session from Open Targets Platform — tagged [RETRIEVED]; verify each in-source before use. 5 figure(s) from curated fixtures carry placeholder citations (TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use.

## 2. Causal question & estimand

Effect = M( system | do(X=a) ) − M( system | do(X=b) ), five slots filled:

- **X (intervened on):** tau
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Causal DAG (adjustment set in words)

- **Exposure X:** tau · **Outcome Y:** Alzheimer's disease
- **Instrument:** germline genotype (fixes direction; used by MR / genetic arms).
- **Adjustment set (back-door):** condition on shared common causes of X and Y (e.g. age, ancestry principal components); **do NOT** condition on downstream mediators or post-onset measurements.
- **Collider (do NOT adjust):** any selection node (survivorship in post-mortem cohorts, cell-line selection) — conditioning on it induces bias.

## 4. Four-explanation checklist

| # | Explanation | Design that addresses it | Status here |
|---|---|---|---|
| 1 | X → Y (causal) | MR + coloc; isogenic KI/rescue | open |
| 2 | Y → X (reverse) | instrument fixed at conception; longitudinal | addressed (genotype fixed at conception) |
| 3 | Z → X, Z → Y (confound) | randomized / MR; conditional KO | addressed by genetic randomization |
| 4 | X → S ← Y (collider) | population sampling; IPW | modeled |

## 5. Evidence FOR

- [UNVERIFIED] **observational_cohort** (association, target_up_disease_up): 1.9 HR per Braak stage (95% CI 1.6-2.3) [human/clinical_outcome]
    - ↳ source: `10.1093/brain/awv050` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - load-bearing assumption(s): no_unmeasured_confounding
- [UNVERIFIED] **formal_mediation** (mediation, target_up_disease_up): no effect size on record [human/clinical_outcome]
    - ↳ source: `10.1002/ana.25395` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - load-bearing assumption(s): no_mediator_outcome_confounding
- [UNVERIFIED] **longitudinal_cohort** (temporal, target_up_disease_up): no effect size on record [human/biomarker]
    - ↳ source: `10.1126/scitranslmed.aau5732` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - load-bearing assumption(s): no_reverse_causation
- [UNVERIFIED] **biochemical_pathway** (mechanism, target_up_disease_up): no effect size on record [human/molecular_profile]
    - ↳ source: `10.1146/annurev-neuro-072116-031153` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 6. Evidence AGAINST / informative nulls

- [RETRIEVED] **observational_cohort** (association, null): 0.374 OT association score (0-1) (no CI)
    - ↳ source: Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession `opentargets_ENSG00000186868` — RETRIEVED live — integrated score, not a primary measurement; verify the underlying datatype evidence in-source before use.
    - Integrated backbone score only. Direction-less by construction; contributes to strength/consistency, never a causal tier. datatype scores: {'literature': 1.0, 'genetic_association': 0.465, 'clinical': 0.19}
- [UNVERIFIED] **gwas_nearest_gene** (genetic, null): no effect size on record
    - ↳ source: `10.1038/ng.2802` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - MAPT mutations cause FTD, not AD. Independent AD-specific genetic support is weak.

## 7. Causal Strength Profile (CSP)

Identification gate: min(A1..A4) = **0** → gated tier **association** (correlation only). Corroboration (B-axes) cannot lift this ceiling.

| Axis | Score (0–3) | Family |
|---|---|---|
| A1 Confounding Robustness | 1 | identification |
| A2 Reverse-Causation Robustness | 3 | identification |
| A3 Selection Robustness | 1 | identification |
| A4 Interventional Directness | 0 | identification |
| B1 Dose-Response Gradient | 0 | corroboration |
| B2 Temporal Precedence | 3 | corroboration |
| B3 Replication Breadth | 0 | corroboration |
| B4 Human Translatability | 3 | corroboration |

## 8. Evidence hierarchy (by dimension tier)

| Dimension | Tier | # items |
|---|---|---|
| association | moderate | 2 |
| genetic | weak | 1 |
| mechanism | moderate | 1 |
| mediation | moderate | 1 |
| temporal | moderate | 1 |

## 9. Data & databases → named gaps

**Sources queried this appraisal:**

- **Hand-curated literature fixture** — C (paper-attached); retrieval: curated offline record. Cite: see per-item DOI/PMID (TODO:cite placeholders).
- **Open Targets Platform** — A (open, keyless); retrieval: live GraphQL query this session. Cite: Ochoa et al., Nucleic Acids Research 51:D1353 (2023) (doi:10.1093/nar/gkac1046).

**Named gaps:**

- No unexamined causal dimensions for this arrow.

## 10. Experimental roadmap

- **Next experiment (weakest, most cheaply strengthened):** Formal mediation of the amyloid->cognition effect through tau with a genotype-anchored instrument, plus an AD-specific (not FTD) genetic test. Necessity/sufficiency for AD is the gap.

## 11. Conclusions


**Known limitations:**
- Effect depends on when you intervene; a static tier has no time axis.
- Driver and mediator are both causal; position is a relation, not a coordinate.
- Total and direct effects diverge; conditioning on a mediator can induce collider bias.
- Subgroup causality: a target causal only in a molecular subset needs (target, disease, subgroup) as the unit.

## 12. References

- [UNVERIFIED] `10.1093/brain/awv050` — 10.1093/brain/awv050 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [RETRIEVED] `10.1093/nar/gkac1046` — retrieved from Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession opentargets_ENSG00000186868, A (open, keyless)
- [UNVERIFIED] `10.1002/ana.25395` — 10.1002/ana.25395 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1038/ng.2802` — 10.1038/ng.2802 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1126/scitranslmed.aau5732` — 10.1126/scitranslmed.aau5732 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1146/annurev-neuro-072116-031153` — 10.1146/annurev-neuro-072116-031153 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
