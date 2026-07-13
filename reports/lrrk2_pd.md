# Causal evidence appraisal — LRRK2 → Parkinson disease

## 1. Verdict (BLUF)

**Headline tier: `likely_causal`** — Strong causal evidence on at least one axis, though short of the full bidirectional-plus-intervention convergence. Probably causal.

- **Structural position:** `upstream_initiator` — An early, upstream cause. Its weak concurrent correlation is the signature of an initiator — not evidence against it.
- **Necessity × sufficiency:** `undetermined` — Necessity/sufficiency not established; loss- and gain-of-function needed.
- **Scope:** unscoped (no context specified -- verdict is not context-conditional)
- **Subordinate confidence:** likely causal, uncalibrated (prior 0.05 from default null base rate for gene-disease pairs) *(never exceeds the tier; digits shown only once calibrated)*

> Strong genetic causal support pairs with weak concurrent correlation, the signature of a node that acts early in the cascade and whose association to the measured outcome decays as causal distance grows. For illustration, amyloid in Alzheimer's disease, an early node whose correlation with late disease severity has decayed with causal distance.

> ⚠️ **Validation required.** 8 figure(s) RETRIEVED live this session from Open Targets (genetics: GWAS / burden / ClinVar), Open Targets Platform, gnomAD — tagged [RETRIEVED]; verify each in-source before use.

## 2. Causal question & estimand

- **X (intervened on):** LRRK2
- **a vs b (contrast):** perturbed vs reference level of the target
- **M (readout):** disease-relevant clinical outcome / endpoint
- **system (held fixed):** unscoped (no context specified -- verdict is not context-conditional)
- **population:** unspecified (flagged: generalization not assumed)

## 3. Evidence FOR

- [RETRIEVED] **rare_penetrant_variant** (genetic, target_up_disease_up): no effect size on record
    - ↳ source: Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession `otgenetics_eva_rs34637584` — RETRIEVED live — directional genetic evidence; the item's primary study PMID should be read in-source, and gene-level direction confirmed with eQTL where inferred.
- [RETRIEVED] **rare_penetrant_variant** (genetic, target_up_disease_up): no effect size on record
    - ↳ source: Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession `otgenetics_eva_rs33939927` — RETRIEVED live — directional genetic evidence; the item's primary study PMID should be read in-source, and gene-level direction confirmed with eQTL where inferred.
- [RETRIEVED] **rare_penetrant_variant** (genetic, target_up_disease_up): no effect size on record
    - ↳ source: Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession `otgenetics_eva_rs34995376` — RETRIEVED live — directional genetic evidence; the item's primary study PMID should be read in-source, and gene-level direction confirmed with eQTL where inferred.
- [RETRIEVED] **rare_penetrant_variant** (genetic, target_up_disease_up): no effect size on record
    - ↳ source: Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession `otgenetics_eva_rs34805604` — RETRIEVED live — directional genetic evidence; the item's primary study PMID should be read in-source, and gene-level direction confirmed with eQTL where inferred.
- [RETRIEVED] **rare_penetrant_variant** (genetic, target_up_disease_up): no effect size on record
    - ↳ source: Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession `otgenetics_eva_rs35801418` — RETRIEVED live — directional genetic evidence; the item's primary study PMID should be read in-source, and gene-level direction confirmed with eQTL where inferred.
- [RETRIEVED] **rare_penetrant_variant** (genetic, target_up_disease_up): no effect size on record
    - ↳ source: Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession `otgenetics_eva_rs35870237` — RETRIEVED live — directional genetic evidence; the item's primary study PMID should be read in-source, and gene-level direction confirmed with eQTL where inferred.

## 4. Evidence AGAINST / informative nulls

- [RETRIEVED] **observational_cohort** (association, null): 0.741 OT association score (0-1) (no CI)
    - ↳ source: Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession `opentargets_ENSG00000188906` — RETRIEVED live — integrated score, not a primary measurement; verify the underlying datatype evidence in-source before use.
- [RETRIEVED] **biochemical_pathway** (mechanism, null): 0.754 LOEUF (no CI)
    - ↳ source: gnomAD (Karczewski et al., Nature 581:434 (2020); doi:10.1038/s41586-020-2308-7), accession `gnomad_constraint_LRRK2` — RETRIEVED live — constraint metric; confirm gene build/version and current gnomAD release before use.

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

- **Open Targets Platform** — A (open, keyless); live GraphQL query this session. Cite: Ochoa et al., Nucleic Acids Research 51:D1353 (2023)
- **Open Targets (genetics: GWAS / burden / ClinVar)** — A (open, keyless); live GraphQL query this session. Cite: Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item
- **gnomAD** — A (open, keyless); live GraphQL query this session. Cite: Karczewski et al., Nature 581:434 (2020)

## 7. What would change the verdict

- **Next experiment:** Strengthen the weakest causal dimension with a genotype-anchored or reversible perturbation test.

## 8. References

- [RETRIEVED] `10.1093/nar/gkac1046` — retrieved from Open Targets Platform (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); doi:10.1093/nar/gkac1046), accession opentargets_ENSG00000188906, A (open, keyless)
- [RETRIEVED] `PMID:15680455` — retrieved from Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession otgenetics_eva_rs34637584, A (open, keyless)
- [RETRIEVED] `PMID:15541308` — retrieved from Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession otgenetics_eva_rs33939927, A (open, keyless)
- [RETRIEVED] `PMID:16157909` — retrieved from Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession otgenetics_eva_rs34995376, A (open, keyless)
- [RETRIEVED] `PMID:15541309` — retrieved from Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession otgenetics_eva_rs34805604, A (open, keyless)
- [RETRIEVED] `PMID:15541308` — retrieved from Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession otgenetics_eva_rs35801418, A (open, keyless)
- [RETRIEVED] `PMID:15541309` — retrieved from Open Targets (genetics: GWAS / burden / ClinVar) (Ochoa et al., Nucleic Acids Research 51:D1353 (2023); primary study PMIDs per item; doi:10.1093/nar/gkac1046), accession otgenetics_eva_rs35870237, A (open, keyless)
- [RETRIEVED] `10.1038/s41586-020-2308-7` — retrieved from gnomAD (Karczewski et al., Nature 581:434 (2020); doi:10.1038/s41586-020-2308-7), accession gnomad_constraint_LRRK2, A (open, keyless)
