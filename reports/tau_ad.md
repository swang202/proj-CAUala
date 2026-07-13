# Causal evidence appraisal — tau → Alzheimer's disease

## 1. Verdict (BLUF)

**Headline tier: `plausible`** — Some causal signal, but only moderate or indirect so far. Worth pursuing; not yet established.

- **Structural position:** `downstream_mediator` — On the causal path but downstream: an excellent biomarker, a more uncertain target. (A mediator is still causal.)
- **Necessity × sufficiency:** `undetermined` — Necessity/sufficiency not established; loss- and gain-of-function needed.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely non-causal, uncalibrated (prior 0.10 from base rate for a strong biomarker with weak disease-specific genetics (curated set)) *(never exceeds the tier; digits shown only once calibrated)*

> Strong association and a plausible mediating position combine with weak independent genetic support: an excellent biomarker but an uncertain target, because a mediator IS causal yet its position in the graph is a relation, not proof of primacy. For illustration, tau in Alzheimer's disease -- it tracks cognitive decline better than amyloid because it sits closer to the effector end of the chain, not because it is more causal.

> ⚠️ **Validation required.** 5 figure(s) from curated fixtures carry placeholder citations (TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use.

## 2. Causal question & estimand

- **X (intervened on):** tau
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Evidence FOR

- [UNVERIFIED] **observational_cohort** (association, target_up_disease_up): 1.9 HR per Braak stage (95% CI 1.6–2.3)
    - ↳ source: `10.1093/brain/awv050` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **formal_mediation** (mediation, target_up_disease_up): no effect size on record
    - ↳ source: `10.1002/ana.25395` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **longitudinal_cohort** (temporal, target_up_disease_up): no effect size on record
    - ↳ source: `10.1126/scitranslmed.aau5732` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **biochemical_pathway** (mechanism, target_up_disease_up): no effect size on record
    - ↳ source: `10.1146/annurev-neuro-072116-031153` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 4. Evidence AGAINST / informative nulls

- [UNVERIFIED] **gwas_nearest_gene** (genetic, null): no effect size on record
    - ↳ source: `10.1038/ng.2802` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 5. Causal Strength Profile (CSP)

Weakest identification axis (A1..A4 min) = **0/3** (Interventional Directness). Identification is the ceiling — corroboration (B-axes) cannot lift a claim past it.

- A1 Confounding Robustness: 1/3 (identification)
- A2 Reverse-Causation Robustness: 3/3 (identification)
- A3 Selection Robustness: 1/3 (identification)
- A4 Interventional Directness: 0/3 (identification)
- B1 Dose-Response Gradient: 0/3 (corroboration)
- B2 Temporal Precedence: 3/3 (corroboration)
- B3 Replication Breadth: 0/3 (corroboration)
- B4 Human Translatability: 3/3 (corroboration)

## 6. Data & databases

- **Hand-curated literature fixture** — C (paper-attached); curated offline record. Cite: see per-item DOI/PMID (TODO:cite placeholders)

## 7. What would change the verdict

- **Next experiment:** Formal mediation of the amyloid->cognition effect through tau with a genotype-anchored instrument, plus an AD-specific (not FTD) genetic test. Necessity/sufficiency for AD is the gap.

## 8. References

- [UNVERIFIED] `10.1093/brain/awv050` — 10.1093/brain/awv050 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1002/ana.25395` — 10.1002/ana.25395 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1038/ng.2802` — 10.1038/ng.2802 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1126/scitranslmed.aau5732` — 10.1126/scitranslmed.aau5732 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1146/annurev-neuro-072116-031153` — 10.1146/annurev-neuro-072116-031153 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
