# Causal Data-Source Catalog & Integration Plan

*Companion to the Report Spec. Purpose: turn each named evidence gap into a concrete, probe-able dataset — always preferring **raw data you can recompute** over quoted numbers. Classifies every source by how the tool reaches it, and lays out what to build.*

Access verified via live search July 2026 (see Sources at end).

---

## 1. Access classes (this is the key distinction for the tool)

| Class | Meaning | Tool can do it… | Auth |
|---|---|---|---|
| **A — Open** | public API or bulk download, no gatekeeping | **now, autonomously** | none / free API key |
| **B — Controlled** | application + Data Use Agreement, runs in an enclave | **plan + point**, a credentialed human runs it | DUA + cloud enclave |
| **C — Paper-attached** | dataset lives in a supplement / GEO / Zenodo tied to one paper | **fetch per-paper**, validate provenance | none, usually |

The rule the tool enforces: **for any headline number, find the Class-A or Class-C raw data behind it and recompute; if the evidence only exists in Class B, say so and produce the analysis plan the credentialed user runs.**

---

## 2. The catalog — grouped by which causal axis they feed

### 2A. Human genetic causal inference (MR, colocalization, fine-mapping) — feeds axes A1, A2, B4

| Source | Class | Holds | Access mechanic | Raw/processed |
|---|---|---|---|---|
| **GWAS Catalog** (EBI) | A | curated GWAS associations, full summary stats | REST API + FTP harmonised sumstats | processed (assoc); raw sumstats downloadable |
| **IEU OpenGWAS** | A* | ~50k harmonised GWAS datasets for MR | `ieugwasr`/`TwoSampleMR` (R) via API; **needs a free JWT token** | processed sumstats |
| **eQTL Catalogue** (EBI) | A | uniformly processed eQTL/sQTL across tissues/cell types | REST API + FTP | processed (nominal + fine-mapped) |
| **GTEx Portal** | A | multi-tissue eQTL, expression | REST API (`gtexr`), open bulk downloads; individual-level via dbGaP (B) | processed open; raw = dbGaP |
| **Open Targets Platform** | A | target–disease evidence incl. genetics (L2G), colocalization | **GraphQL API**; BigQuery/Parquet bulk | processed, integrated |
| **gnomAD** | A | population allele freq, constraint (pLI/LOEUF) | GraphQL API + bulk VCF | processed |
| **ClinVar / ClinGen** | A | variant pathogenicity, gene–disease validity | E-utilities / FTP; ClinGen API | curated |
| **FinnGen / GP2** | A/B | large PD & general GWAS (GP2 = diverse-ancestry PD) | FinnGen public sumstats (A); GP2 tiered (B) | processed |

*OpenGWAS is open but rate-limited and token-gated — treat as A with an API key.

**What the tool computes here:** two-sample MR (`TwoSampleMR` + MR-Egger/weighted-median/MR-PRESSO for pleiotropy), colocalization (`coloc`/`SuSiE-coloc`, PP4), fine-mapping (SuSiE/FINEMAP), instrument PheWAS for the exclusion restriction. **This is the single highest-value automated capability** — it is the axis-A1/A2 evidence that was "NOT DONE" in every one of your reports.

### 2B. Perturbation / interventional transcriptomics — feeds axes A4 (directness), B1 (dose-response)

| Source | Class | Holds | Access mechanic | Raw/processed |
|---|---|---|---|---|
| **LINCS L1000 / CMap (clue.io)** | A | ~1.3M drug/shRNA/ORF signatures | clue.io API (free reg + key); GCTx bulk; **also mirrored in GEO** (GSE92742, GSE70138) | Level 2 raw → Level 5 signatures |
| **scPerturb** | A / C | harmonised single-cell Perturb-seq/CRISPR-screen datasets | download `.h5ad` (scperturb.org / Zenodo) | processed counts, harmonised |
| **DepMap** (Broad) | A | genome-wide CRISPR KO fitness (Chronos), RNAi, omics across ~1000 lines | portal CSV + figshare per quarterly release | processed gene-effect matrices |
| **Individual Perturb-seq papers** | C | e.g. genome-scale Perturb-seq | GEO/SRA accession in the paper | **raw counts** — recompute DE |
| **BioGRID ORCS** | A | CRISPR screen hits, curated | REST API / download | processed |

**What the tool computes:** L1000 connectivity (does perturbing gene X move a disease signature? `cmapPy`), Perturb-seq differential expression per guide (`scanpy`/`scvi-tools`), dose-response from allelic/CRISPRa-i series. This is the *bench `do(X)`* evidence — axis A4.

### 2C. Expression / single-cell context — feeds axes B2 (temporality), B4, specificity

| Source | Class | Holds | Access mechanic | Raw/processed |
|---|---|---|---|---|
| **NCBI GEO** | A / C | the universal repository; series behind most papers | E-utilities (Entrez); `GEOparse`; FTP for supplementary; **SRA for raw FASTQ** | series matrix (processed) + raw |
| **ArrayExpress / BioStudies** (EBI) | A / C | EU-side expression archive | BioStudies API + FTP | processed + raw |
| **CZ CELLxGENE Census** | A | ~standardised single-cell atlas, tens of millions of cells | Python/R `cellxgene-census` (TileDB-SOMA) on AWS | processed counts + metadata |
| **Allen Brain / SEA-AD** | A | region- and cell-type-resolved brain expression, AD atlas | portal downloads + API | processed |
| **Human Cell Atlas / HCA DCP** | A | raw + processed single-cell matrices | DCP API / DSS | both |

**What the tool computes:** cell-type specificity of a gene (is p53 elevated *only* in DA neurons?), RNA-velocity temporal ordering in iPSC time-courses (`scVelo`/`veloVI`), reprocessing a GEO series from raw to check a DE claim.

### 2D. Longitudinal human cohorts (temporality, biomarkers) — feeds axes B2, A3

| Source | Class | Holds | Access mechanic | Raw/processed |
|---|---|---|---|---|
| **AMP-AD / AD Knowledge Portal** | **B** | ROSMAP, MSBB, Mayo — multi-omics + neuropath | **Synapse** + Data Use Certificate; `synapseclient` (Py/R/CLI) | raw + processed, controlled |
| **AMP-PD** | **B** | harmonised PD cohorts, WGS, RNA-seq, clinical | **Terra** (GCP) after registration + DUA; BigQuery/GCS in-enclave | raw + processed, controlled |
| **PPMI / BioFINDER / DIAN / ADNI** | B | prospective biomarker trajectories (tau/αsyn PET, CSF) | per-study application + portal | processed + some raw |
| **UK Biobank** | B | 500k deep-phenotyped, imaging, WES/WGS | application + DNAnexus RAP (in-enclave) | raw + processed |
| **dbGaP / EGA** | B | controlled individual-level genotype/omics | DAC approval; `prefetch`/EGA client | raw |

**Boundary rule:** the tool **cannot** pull Class-B individual-level data on its own. It produces (a) the exact query/analysis to run, (b) the cohort + data-dictionary variables needed, (c) the enclave (Synapse/Terra/DNAnexus) it runs in — for a credentialed human to execute. Summary-level AMP-AD/PD outputs that are already public *can* be cited (Class A) with provenance.

### 2E. Mechanism / molecular — feeds specificity, plausibility

| Source | Class | Access | Use |
|---|---|---|---|
| **STRING, BioGRID, IntAct** | A | REST/download | interaction/mediation candidates |
| **Reactome, KEGG** | A | API/download | pathway topology → mediation priors |
| **UniProt, PDB, AlphaFold DB, PhosphoSitePlus** | A | REST/download | protein/PTM/structural grounding |
| **PRIDE / ProteomeXchange** | A / C | API/FTP | total-protein vs PTM proteomics (the APP-tau "total tau" gap) |

---

## 3. Raw-data-first validation protocol (the tool must follow this)

For every headline quantitative claim:

1. **Locate the primary dataset** (accession: GSE…, dbGaP phs…, Synapse syn…, Zenodo DOI, clue.io sig id). Record it.
2. **Prefer raw** — FASTQ/counts/Level-2, not the paper's summary table. If only processed exists, note it.
3. **Recompute the statistic** with a standard pipeline (below) and compare to the claimed value.
4. **Sanity-check the pipeline invariants**: genome build (GRCh37 vs 38), gene-ID namespace, normalization, batch/covariate model, multiple-testing, effect-allele orientation (MR), tissue/cell-type match.
5. **Capture provenance**: accession + version + checksum + access date → into the `[VERIFIED]` tag.
6. **Report agreement or discrepancy**, not just the recomputed number. A mismatch is itself a finding.

Standard compute stack the tool calls (much already in this workspace's `bio-research` plugin):

- Bulk RNA-seq reprocessing → **`nextflow-development`** skill (nf-core/rnaseq) from GEO/SRA FASTQ.
- Differential expression → DESeq2 / limma-voom.
- Single-cell / Perturb-seq → scanpy, **`scvi-tools`** skill, **`single-cell-rna-qc`** skill.
- MR → `TwoSampleMR` + `ieugwasr`; coloc → `coloc`/`SuSiE`.
- L1000 → `cmapPy` connectivity scoring.
- Instrument standardisation → **`instrument-data-to-allotrope`** skill.

---

## 4. What to build to incorporate these (integration plan)

**Layer 1 — Source registry.** One config entry per source: `{id, access_class, auth_method, endpoint, query_fn, raw_available, license, id_namespace}`. The report generator reads this so "databases → named gaps" (Spec §9) is auto-populated with the correct access class.

**Layer 2 — Auth & clients.** Provision: Entrez API key (GEO/E-utilities), OpenGWAS JWT, clue.io key, Synapse PAT, Terra/Firecloud + GCP creds, DNAnexus token. Class-A clients run in this container; Class-B clients only inside the user's enclave.

**Layer 3 — Retrieval + validation service.** Implements §3: accession resolver → raw fetch → recompute → invariant checks → provenance record. Emits the `[VERIFIED]`/`[RETRIEVED]` tag the report consumes.

**Layer 4 — Compute adapters.** Wrap MR, coloc, DE, connectivity, velocity as callable jobs, each returning a result + the CSP axis it satisfies (e.g. an MR result raises A1/A2 to 3).

**Layer 5 — Controlled-access handoff.** For Class-B: generate the analysis script + variable list + enclave target, package it for a credentialed run, ingest the returned summary. Never block the report on it — mark the gap "requires credentialed enclave."

**Connectors worth adding now:** several of these have community MCP servers / Claude skills (GEO, DepMap, cellxgene-census). Wiring them as connectors gives the tool live query without bespoke code. Say the word and I'll search the connector registry and wire up the ones that exist.

---

## 5. Priority recommendation

If you build in one order: **(1) OpenGWAS + eQTL Catalogue + coloc/MR** (turns the "MR NOT DONE" gap in every report into an automated result — highest causal leverage), then **(2) GEO/SRA raw reprocessing** (validates the expression claims), then **(3) LINCS + scPerturb/DepMap** (adds bench `do(X)` evidence), then **(4) the Class-B handoff** for AMP-AD/PD/UKB where the definitive human data lives. The first three are Class-A — the tool can do them autonomously today.

---

### Sources
- [AD Knowledge Portal — Data Access (Synapse)](https://adknowledgeportal.synapse.org/DataAccess/Instructions) · [Data Use Certificates](https://help.adknowledgeportal.org/apd/Data-Use-Certificates.2623373330.html)
- [AMP-PD registration/access](https://amp-pd.org/request-registration-or-renewal) · [AMP-PD Terra tools](https://amp-pdrd.org/tools)
- [LINCS CMap L1000 downloads (clue.io)](https://clue.io/connectopedia/lincs_cmap_data) · [clue.io developer resources](https://clue.io/developer-resources)
- [Open Targets GraphQL API](https://platform-docs.opentargets.org/data-access/graphql-api)
- [scPerturb (Nature Methods)](https://www.nature.com/articles/s41592-023-02144-y)
- [CZ CELLxGENE Census docs](https://chanzuckerberg.github.io/cellxgene-census/)
- [IEU OpenGWAS / ieugwasr](https://mrcieu.github.io/ieugwasr/) · [TwoSampleMR](https://mrcieu.github.io/TwoSampleMR/)
- [DepMap data downloads](https://depmap.org/portal/data_page/?tab=currentRelease)
- [eQTL Catalogue data access (EBI)](https://www.ebi.ac.uk/eqtl/Data_access/) · [GTEx API](https://gtexportal.org/home/apiPage)
- [Programmatic access to GEO (NCBI)](https://www.ncbi.nlm.nih.gov/geo/info/geo_paccess.html)
