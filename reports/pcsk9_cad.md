# Causal evidence appraisal — PCSK9 → coronary artery disease

## 1. Verdict (BLUF)

**Headline tier: `causal_driver`** — Converging causal evidence — bidirectional genetics plus a successful human intervention. This behaves like a genuine driver you can act on.

- **Structural position:** `validated_driver` — A validated driver: loss- and gain-of-function point opposite ways and a human intervention worked.
- **Necessity × sufficiency:** `necessary_and_sufficient` — Monogenic-like: alone required and enough. Rare.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely causal, uncalibrated (prior 0.05 from base rate for a randomly chosen gene-disease pair (curated set)) *(never exceeds the tier; digits shown only once calibrated)*

> Converging bidirectional causal evidence -- loss- and gain-of-function pointing opposite ways -- together with a successful human intervention place the target on the causal path with the strongest support the framework assigns. For illustration, PCSK9 in coronary disease -- loss-of-function alleles protect, gain-of-function causes familial hypercholesterolemia, and PCSK9 inhibitors cut events in outcome trials.

> ⚠️ **Validation required.** 5 figure(s) from curated fixtures carry placeholder citations (TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use.

## 2. Causal question & estimand

- **X (intervened on):** PCSK9
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Evidence FOR

- [UNVERIFIED] **protective_allele** (genetic, target_down_disease_down): 0.12 OR (95% CI 0.03–0.45)
    - ↳ source: `PMID:16554528` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **rare_penetrant_variant** (genetic, target_up_disease_up): 2.8 OR (95% CI 1.9–4.1)
    - ↳ source: `10.1038/ng1161` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **human_rct** (intervention, target_down_disease_down): 0.85 HR (95% CI 0.79–0.92)
    - ↳ source: `PMID:28304224` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **human_rct** (intervention, target_down_disease_down): 0.85 HR (95% CI 0.78–0.93)
    - ↳ source: `PMID:30403574` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **biochemical_pathway** (mechanism, target_up_disease_up): no effect size on record
    - ↳ source: `10.1074/jbc.M311730200` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 4. Evidence AGAINST / informative nulls

- No informative nulls on record.

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
- Gap — association: not queried. Verdict is at an extreme (causal_driver); no remaining modality's maximum plausible weight could flip it.

## 7. What would change the verdict

- **Next experiment:** None needed for causal status; bidirectional genetics and two positive outcome trials already converge. Remaining question is dose/timing optimization.

## 8. References

- [UNVERIFIED] `PMID:16554528` — PMID:16554528 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1038/ng1161` — 10.1038/ng1161 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `PMID:28304224` — PMID:28304224 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `PMID:30403574` — PMID:30403574 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1074/jbc.M311730200` — 10.1074/jbc.M311730200 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
