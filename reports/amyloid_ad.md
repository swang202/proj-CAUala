# Causal evidence appraisal — APP/amyloid → Alzheimer's disease

## 1. Verdict (BLUF)

**Headline tier: `likely_causal`** — Strong causal evidence on at least one axis, though short of the full bidirectional-plus-intervention convergence. Probably causal.

- **Structural position:** `upstream_initiator` — An early, upstream cause. Its weak concurrent correlation is the signature of an initiator — not evidence against it.
- **Necessity × sufficiency:** `necessary_and_sufficient` — Monogenic-like: alone required and enough. Rare.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely causal, uncalibrated (prior 0.10 from base rate for a gene with prior monogenic evidence (curated set)) *(never exceeds the tier; digits shown only once calibrated)*

> Strong genetic causal support pairs with weak concurrent correlation, the signature of a node that acts early in the cascade and whose association to the measured outcome decays as causal distance grows. For illustration, amyloid in Alzheimer's disease -- bidirectional genetics, changes decades before symptoms, yet weak concurrent correlation with cognition.

> ⚠️ **Validation required.** 2 figure(s) RETRIEVED live this session from Open Targets Platform, gnomAD — tagged [RETRIEVED]; verify each in-source before use. 6 figure(s) from curated fixtures carry placeholder citations (TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use.

## 2. Causal question & estimand

- **X (intervened on):** APP/amyloid
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Evidence FOR

- [UNVERIFIED] **rare_penetrant_variant** (genetic, target_up_disease_up): no effect size on record
    - ↳ source: `10.1038/349704a0` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **protective_allele** (genetic, target_down_disease_down): no effect size on record
    - ↳ source: `10.1038/nature11283` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **cross_sectional** (association, target_up_disease_up): no effect size on record
    - ↳ source: `10.1212/WNL.0b013e31820af900` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **anchored_onset_cohort** (temporal, target_up_disease_up): no effect size on record
    - ↳ source: `10.1056/NEJMoa1202753` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **human_rct** (intervention, target_down_disease_down): no effect size on record
    - ↳ source: `10.1056/NEJMoa2212948` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.
- [UNVERIFIED] **biochemical_pathway** (mechanism, target_up_disease_up): no effect size on record
    - ↳ source: `10.15252/emmm.201606210` (primary paper) — UNVERIFIED — placeholder citation (TODO:cite); replace from the primary paper before any real use.

## 4. Evidence AGAINST / informative nulls

- [RETRIEVED] **observational_cohort** (association, null): 0.807 OT association score (0-1) (no CI)
    - ↳ source: Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession `opentargets_ENSG00000142192` — RETRIEVED live — integrated score, not a primary measurement; verify the underlying datatype evidence in-source before use.
- [RETRIEVED] **biochemical_pathway** (mechanism, null): 0.413 LOEUF (no CI)
    - ↳ source: gnomAD (Karczewski et al., Nature 581:434 (2020); doi:10.1038/s41586-020-2308-7), accession `gnomad_constraint_APP` — RETRIEVED live — constraint metric; confirm gene build/version and current gnomAD release before use.

## 5. Causal Strength Profile (CSP)

Weakest identification axis (A1..A4 min) = **2/3** (Selection Robustness, Interventional Directness). Identification is the ceiling — corroboration (B-axes) cannot lift a claim past it.

- A1 Confounding Robustness: 3/3 (identification)
- A2 Reverse-Causation Robustness: 3/3 (identification)
- A3 Selection Robustness: 2/3 (identification)
- A4 Interventional Directness: 2/3 (identification)
- B1 Dose-Response Gradient: 0/3 (corroboration)
- B2 Temporal Precedence: 3/3 (corroboration)
- B3 Replication Breadth: 0/3 (corroboration)
- B4 Human Translatability: 3/3 (corroboration)

## 6. Data & databases

- **Hand-curated literature fixture** — C (paper-attached); curated offline record. Cite: see per-item DOI/PMID (TODO:cite placeholders)
- **Open Targets Platform** — A (open, keyless); live GraphQL query this session. Cite: Ochoa et al., Nucleic Acids Research 51:D1353 (2023)
- **gnomAD** — A (open, keyless); live GraphQL query this session. Cite: Karczewski et al., Nature 581:434 (2020)

## 7. What would change the verdict

- **Next experiment:** A prevention-arm trial in mutation carriers (do(clear amyloid) BEFORE symptom onset). The modest late-intervention benefit is exactly what an early initiator predicts; the untested contrast is early intervention.

## 8. References

- [UNVERIFIED] `10.1038/349704a0` — 10.1038/349704a0 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1038/nature11283` — 10.1038/nature11283 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1212/WNL.0b013e31820af900` — 10.1212/WNL.0b013e31820af900 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [RETRIEVED] `10.1093/nar/gkac1046` — retrieved from Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession opentargets_ENSG00000142192, A (open, keyless)
- [UNVERIFIED] `10.1056/NEJMoa1202753` — 10.1056/NEJMoa1202753 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.1056/NEJMoa2212948` — 10.1056/NEJMoa2212948 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [UNVERIFIED] `10.15252/emmm.201606210` — 10.15252/emmm.201606210 (primary; Hand-curated literature fixture, C (paper-attached)) [UNVERIFIED]
- [RETRIEVED] `10.1038/s41586-020-2308-7` — retrieved from gnomAD (Karczewski et al., Nature 581:434 (2020); doi:10.1038/s41586-020-2308-7), accession gnomad_constraint_APP, A (open, keyless)
