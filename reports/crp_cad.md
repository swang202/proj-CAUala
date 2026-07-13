# Causal evidence appraisal — CRP → coronary artery disease

## 1. Verdict (BLUF)

**Headline tier: `likely_noncausal`** — The causal tests that exist point away from causation. Probably not a driver.

- **Structural position:** `displaced_signal` — The correlation is real, but the causal signal lives one node upstream in the same pathway. You would be targeting the reporter, not the source.
- **Necessity × sufficiency:** `undetermined` — Necessity/sufficiency not established; loss- and gain-of-function needed.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely non-causal, uncalibrated (prior 0.05 from base rate for a randomly chosen biomarker-disease pair (curated set)) *(never exceeds the tier; digits shown only once calibrated)*

> The measured node correlates while its own genetic evidence is null, and a neighbouring node in the same pathway carries the causal signal, so the real association is displaced from the true upstream driver. For illustration, CRP versus IL-6 in coronary disease -- CRP correlates but its variants are null, while the causal signal sits one node upstream at the IL-6 receptor.

> ⚠️ **Validation required.** 3 figure(s) from curated fixtures carry placeholder citations (TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use.

## 2. Causal question & estimand

- **X (intervened on):** CRP
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Evidence FOR

- [UNVERIFIED] **observational_cohort** (association, target_up_disease_up): 1.5 HR per SD (95% CI 1.31–1.72)
    - ↳ source: `10.1016/S0140-6736(09)61717-7` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **biochemical_pathway** (mechanism, target_up_disease_up): no effect size on record
    - ↳ source: `10.1038/nri.2017.103` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 4. Evidence AGAINST / informative nulls

- [UNVERIFIED] **mendelian_randomization** (genetic, null): 1.0 OR per SD (95% CI 0.9–1.13) [crosses null]
    - ↳ source: `10.1136/bmj.d548` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 5. Causal Strength Profile (CSP)

Weakest identification axis (A1..A4 min) = **1/3** (Selection Robustness, Interventional Directness). Identification is the ceiling — corroboration (B-axes) cannot lift a claim past it.

- A1 Confounding Robustness: 3/3 (identification)
- A2 Reverse-Causation Robustness: 3/3 (identification)
- A3 Selection Robustness: 1/3 (identification)
- A4 Interventional Directness: 1/3 (identification)
- B1 Dose-Response Gradient: 0/3 (corroboration)
- B2 Temporal Precedence: 0/3 (corroboration)
- B3 Replication Breadth: 0/3 (corroboration)
- B4 Human Translatability: 3/3 (corroboration)

## 6. Data & databases

- **Hand-curated literature fixture** — C (paper-attached); curated offline record. Cite: see per-item DOI/PMID (TODO:cite placeholders)

## 7. What would change the verdict

- **Next experiment:** Colocalize and MR the IL6R locus against CHD; the causal test belongs on the upstream node (IL-6 signalling), not on CRP itself. CRP-specific instruments are already null.
- Conflict: Association is directional but genetics is null/contradicted: the correlation is real, its causal reading is not.

## 8. References

- [UNVERIFIED] `10.1016/S0140-6736(09)61717-7` — 10.1016/S0140-6736(09)61717-7 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1136/bmj.d548` — 10.1136/bmj.d548 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1038/nri.2017.103` — 10.1038/nri.2017.103 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
