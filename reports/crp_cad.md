# Causal evidence appraisal — CRP → coronary artery disease

## 1. Verdict (BLUF)

**Headline tier: `likely_noncausal`** — the gated ordinal verdict.

- **Structural position:** `displaced_signal`
- **Necessity × sufficiency:** `undetermined` — Necessity/sufficiency not established; loss- and gain-of-function needed.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely non-causal, uncalibrated (prior 0.05 from base rate for a randomly chosen biomarker-disease pair (curated set)) *(never exceeds the tier; digits shown only once calibrated)*

> The measured node correlates while its own genetic evidence is null, and a neighbouring node in the same pathway carries the causal signal, so the real association is displaced from the true upstream driver. For illustration, CRP versus IL-6 in coronary disease -- CRP correlates but its variants are null, while the causal signal sits one node upstream at the IL-6 receptor.

**One-line:** displaced_signal [undetermined] | scope: unscoped (no context specified -- verdict is not context-conditional) | tier: likely_noncausal | likely non-causal, uncalibrated (prior 0.05 from base rate for a randomly chosen biomarker-disease pair (curated set))

> ⚠️ **Validation required.** 2 figure(s) RETRIEVED live this session from Open Targets Platform, gnomAD — tagged [RETRIEVED]; verify each in-source before use. 3 figure(s) from curated fixtures carry placeholder citations (TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use.

## 2. Causal question & estimand

Effect = M( system | do(X=a) ) − M( system | do(X=b) ), five slots filled:

- **X (intervened on):** CRP
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Causal DAG (adjustment set in words)

- **Exposure X:** CRP · **Outcome Y:** coronary artery disease
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

- [UNVERIFIED] **observational_cohort** (association, target_up_disease_up): 1.5 HR per SD (95% CI 1.31-1.72) [human/clinical_outcome]
    - ↳ source: `10.1016/S0140-6736(09)61717-7` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - load-bearing assumption(s): no_unmeasured_confounding
- [UNVERIFIED] **biochemical_pathway** (mechanism, target_up_disease_up): no effect size on record [human/molecular_profile]
    - ↳ source: `10.1038/nri.2017.103` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 6. Evidence AGAINST / informative nulls

- [RETRIEVED] **observational_cohort** (association, null): 0.12 OT association score (0-1) (no CI)
    - ↳ source: Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession `opentargets_ENSG00000132693` — RETRIEVED live — integrated score, not a primary measurement; verify the underlying datatype evidence in-source before use.
    - Integrated backbone score only. Direction-less by construction; contributes to strength/consistency, never a causal tier. datatype scores: {'literature': 0.984}
- [UNVERIFIED] **mendelian_randomization** (genetic, null): 1.0 OR per SD (95% CI 0.9-1.13) [crosses null]
    - ↳ source: `10.1136/bmj.d548` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
    - IL6R variants, by contrast, ARE associated with CHD risk.
- [RETRIEVED] **biochemical_pathway** (mechanism, null): 3.992 LOEUF (no CI)
    - ↳ source: gnomAD (Karczewski et al., Nature 581:434 (2020); doi:10.1038/s41586-020-2308-7), accession `gnomad_constraint_CRP` — RETRIEVED live — constraint metric; confirm gene build/version and current gnomAD release before use.
    - gnomAD GRCh38 constraint: LOEUF=3.9915137588260046, pLI=0.0007593093562352715. LOF-tolerant (unconstrained; haploinsufficiency less likely). Plausibility only -- cannot raise the causal tier (invariant #2).

## 7. Causal Strength Profile (CSP)

Identification gate: min(A1..A4) = **1** → gated tier **suggestive** (association + mechanism). Corroboration (B-axes) cannot lift this ceiling.

| Axis | Score (0–3) | Family |
|---|---|---|
| A1 Confounding Robustness | 3 | identification |
| A2 Reverse-Causation Robustness | 3 | identification |
| A3 Selection Robustness | 1 | identification |
| A4 Interventional Directness | 1 | identification |
| B1 Dose-Response Gradient | 0 | corroboration |
| B2 Temporal Precedence | 0 | corroboration |
| B3 Replication Breadth | 0 | corroboration |
| B4 Human Translatability | 3 | corroboration |

## 8. Evidence hierarchy (by dimension tier)

| Dimension | Tier | # items |
|---|---|---|
| association | moderate | 2 |
| genetic | contradicted | 1 |
| mechanism | moderate | 2 |

## 9. Data & databases → named gaps

**Sources queried this appraisal:**

- **Hand-curated literature fixture** — C (paper-attached); retrieval: curated offline record. Cite: see per-item DOI/PMID (TODO:cite placeholders).
- **Open Targets Platform** — A (open, keyless); retrieval: live GraphQL query this session. Cite: Ochoa et al., Nucleic Acids Research 51:D1353 (2023) (doi:10.1093/nar/gkac1046).
- **gnomAD** — A (open, keyless); retrieval: live GraphQL query this session. Cite: Karczewski et al., Nature 581:434 (2020) (doi:10.1038/s41586-020-2308-7).

**Named gaps:**

- No unexamined causal dimensions for this arrow.

## 10. Experimental roadmap

- **Next experiment (weakest, most cheaply strengthened):** Colocalize and MR the IL6R locus against CHD; the causal test belongs on the upstream node (IL-6 signalling), not on CRP itself. CRP-specific instruments are already null.

## 11. Conclusions

**Conflicts (surfaced, never averaged):**
- Association is directional but genetics is null/contradicted: the correlation is real, its causal reading is not.

**Known limitations:**
- Effect depends on when you intervene; a static tier has no time axis.
- Driver and mediator are both causal; position is a relation, not a coordinate.
- Total and direct effects diverge; conditioning on a mediator can induce collider bias.
- Subgroup causality: a target causal only in a molecular subset needs (target, disease, subgroup) as the unit.

## 12. References

- [UNVERIFIED] `10.1016/S0140-6736(09)61717-7` — 10.1016/S0140-6736(09)61717-7 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [RETRIEVED] `10.1093/nar/gkac1046` — retrieved from Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession opentargets_ENSG00000132693, A (open, keyless)
- [UNVERIFIED] `10.1136/bmj.d548` — 10.1136/bmj.d548 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1038/nri.2017.103` — 10.1038/nri.2017.103 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [RETRIEVED] `10.1038/s41586-020-2308-7` — retrieved from gnomAD (Karczewski et al., Nature 581:434 (2020); doi:10.1038/s41586-020-2308-7), accession gnomad_constraint_CRP, A (open, keyless)
