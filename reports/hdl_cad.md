# Causal evidence appraisal — HDL-C → coronary artery disease

## 1. Verdict (BLUF)

**Headline tier: `refuted`** — the gated ordinal verdict.

- **Structural position:** `associated_noncausal`
- **Necessity × sufficiency:** `undetermined` — Necessity/sufficiency not established; loss- and gain-of-function needed.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely non-causal, uncalibrated (prior 0.05 from base rate for a randomly chosen biomarker-disease pair (curated set)) *(never exceeds the tier; digits shown only once calibrated)*

> Strong, replicated association coexists with null or contradicted genetic and interventional evidence, the signature of a marker, not target: it tracks the outcome without sitting on any causal path to it. For illustration, HDL cholesterol in coronary disease -- decades of clean epidemiology, null Mendelian randomization, and three failed CETP-inhibitor trials.

**One-line:** associated_noncausal [undetermined] | scope: unscoped (no context specified -- verdict is not context-conditional) | tier: refuted | likely non-causal, uncalibrated (prior 0.05 from base rate for a randomly chosen biomarker-disease pair (curated set))

> ⚠️ **Validation required.** 4 figure(s) from curated fixtures carry placeholder citations (TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use.

## 2. Causal question & estimand

Effect = M( system | do(X=a) ) − M( system | do(X=b) ), five slots filled:

- **X (intervened on):** HDL-C
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Causal DAG (adjustment set in words)

- **Exposure X:** HDL-C · **Outcome Y:** coronary artery disease
- **Instrument:** germline genotype (fixes direction; used by MR / genetic arms).
- **Adjustment set (back-door):** condition on shared common causes of X and Y (e.g. age, ancestry principal components); **do NOT** condition on downstream mediators or post-onset measurements.
- **Collider (do NOT adjust):** any selection node (survivorship in post-mortem cohorts, cell-line selection) — conditioning on it induces bias.

## 4. Four-explanation checklist

| # | Explanation | Design that addresses it | Status here |
|---|---|---|---|
| 1 | X → Y (causal) | MR + coloc; isogenic KI/rescue | open |
| 2 | Y → X (reverse) | instrument fixed at conception; longitudinal | addressed (genotype fixed at conception) |
| 3 | Z → X, Z → Y (confound) | randomized / MR; conditional KO | addressed by genetic randomization |
| 4 | X → S ← Y (collider) | population sampling; IPW | acknowledged, not fully modeled |

## 5. Evidence FOR

- [UNVERIFIED] **observational_cohort** (association, target_up_disease_down): 0.78 HR per SD (95% CI 0.74-0.82) [human/clinical_outcome]
    - ↳ source: `PMID:2642759` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - load-bearing assumption(s): no_unmeasured_confounding
- [UNVERIFIED] **biochemical_pathway** (mechanism, target_up_disease_down): no effect size on record [human/molecular_profile]
    - ↳ source: `10.1161/CIRCRESAHA.111.258673` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 6. Evidence AGAINST / informative nulls

- [UNVERIFIED] **mendelian_randomization** (genetic, null): 0.98 OR per SD (95% CI 0.91-1.06) [crosses null]
    - ↳ source: `10.1016/S0140-6736(12)60312-2` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **human_rct** (intervention, null): 1.02 HR (95% CI 0.93-1.12) [crosses null]
    - ↳ source: `PMID:17984165` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - Raised HDL substantially, no benefit. torcetrapib had off-target BP effects; dalcetrapib and evacetrapib were cleaner and still null.

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
| genetic | contradicted | 1 |
| intervention | contradicted | 1 |
| mechanism | moderate | 1 |

## 9. Data & databases → named gaps

**Sources queried this appraisal:**

- **Hand-curated literature fixture** — C (paper-attached); retrieval: curated offline record. Cite: see per-item DOI/PMID (TODO:cite placeholders).

**Named gaps:**

- No unexamined causal dimensions for this arrow.

## 10. Experimental roadmap

- **Next experiment (weakest, most cheaply strengthened):** None would change the verdict: a pleiotropy-robust MR and three CETP-inhibitor outcome trials are already null. The marker is real; the target is not.

## 11. Conclusions

**Conflicts (surfaced, never averaged):**
- Association is directional but genetics is null/contradicted: the correlation is real, its causal reading is not.

**Known limitations:**
- Effect depends on when you intervene; a static tier has no time axis.
- Driver and mediator are both causal; position is a relation, not a coordinate.
- Total and direct effects diverge; conditioning on a mediator can induce collider bias.
- Subgroup causality: a target causal only in a molecular subset needs (target, disease, subgroup) as the unit.

## 12. References

- [UNVERIFIED] `PMID:2642759` — PMID:2642759 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1016/S0140-6736(12)60312-2` — 10.1016/S0140-6736(12)60312-2 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `PMID:17984165` — PMID:17984165 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1161/CIRCRESAHA.111.258673` — 10.1161/CIRCRESAHA.111.258673 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
