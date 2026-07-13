# Causal evidence appraisal — HDL-C → coronary artery disease

## 1. Verdict (BLUF)

**Headline tier: `refuted`** — A causal test was performed and failed (a trial, or clean genetics pointing the other way). The causal hypothesis is contradicted.

- **Structural position:** `associated_noncausal` — A marker — it tracks the disease but sits on no causal path. Real correlation, no causation.
- **Necessity × sufficiency:** `undetermined` — Necessity/sufficiency not established; loss- and gain-of-function needed.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely non-causal, uncalibrated (prior 0.05 from base rate for a randomly chosen biomarker-disease pair (curated set)) *(never exceeds the tier; digits shown only once calibrated)*

> Strong, replicated association coexists with null or contradicted genetic and interventional evidence, the signature of a marker, not target: it tracks the outcome without sitting on any causal path to it. For illustration, HDL cholesterol in coronary disease -- decades of clean epidemiology, null Mendelian randomization, and three failed CETP-inhibitor trials.

> ⚠️ **Validation required.** 4 figure(s) from curated fixtures carry placeholder citations (TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use.

## 2. Causal question & estimand

- **X (intervened on):** HDL-C
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Evidence FOR

- [UNVERIFIED] **observational_cohort** (association, target_up_disease_down): 0.78 HR per SD (95% CI 0.74–0.82)
    - ↳ source: `PMID:2642759` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **biochemical_pathway** (mechanism, target_up_disease_down): no effect size on record
    - ↳ source: `10.1161/CIRCRESAHA.111.258673` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 4. Evidence AGAINST / informative nulls

- [UNVERIFIED] **mendelian_randomization** (genetic, null): 0.98 OR per SD (95% CI 0.91–1.06) [crosses null]
    - ↳ source: `10.1016/S0140-6736(12)60312-2` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **human_rct** (intervention, null): 1.02 HR (95% CI 0.93–1.12) [crosses null]
    - ↳ source: `PMID:17984165` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 5. Causal Strength Profile (CSP)

Weakest identification axis (A1..A4 min) = **2/3** (Selection Robustness, Interventional Directness). Identification is the ceiling — corroboration (B-axes) cannot lift a claim past it.

- A1 Confounding Robustness: 3/3 (identification)
- A2 Reverse-Causation Robustness: 3/3 (identification)
- A3 Selection Robustness: 2/3 (identification)
- A4 Interventional Directness: 2/3 (identification)
- B1 Dose-Response Gradient: 0/3 (corroboration)
- B2 Temporal Precedence: 0/3 (corroboration)
- B3 Replication Breadth: 0/3 (corroboration)
- B4 Human Translatability: 3/3 (corroboration)

## 6. Data & databases

- **Hand-curated literature fixture** — C (paper-attached); curated offline record. Cite: see per-item DOI/PMID (TODO:cite placeholders)

## 7. What would change the verdict

- **Next experiment:** None would change the verdict: a pleiotropy-robust MR and three CETP-inhibitor outcome trials are already null. The marker is real; the target is not.
- Conflict: Association is directional but genetics is null/contradicted: the correlation is real, its causal reading is not.

## 8. References

- [UNVERIFIED] `PMID:2642759` — PMID:2642759 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1016/S0140-6736(12)60312-2` — 10.1016/S0140-6736(12)60312-2 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `PMID:17984165` — PMID:17984165 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1161/CIRCRESAHA.111.258673` — 10.1161/CIRCRESAHA.111.258673 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
