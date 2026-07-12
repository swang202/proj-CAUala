# proj-CAUala — Engineering Build Brief

> 🧭 **Build — the engineering spec.** How the tool is designed and constructed. For *what actually shipped* (and how to run it), read [IMPLEMENTATION.md](IMPLEMENTATION.md); to add a data source, [docs/CONNECTORS.md](docs/CONNECTORS.md). Full map: **[docs/README.md](docs/README.md)**.

**Audience:** the developer or coding agent who will build the tool.
**Prereqs (read in this order):** `CONCEPTS.md` (the causal reasoning), `DESIGN.md`
(the reconciled spec — the arbiter when anything conflicts), `memo.md` (motivation),
`src/schema.py` + `tests/test_known_answers.py` (the data model, already built and
passing). Skim `CAUala-critique.md` for the reasoning constraints.

**One-line spec:** *given a biological causal question `A → B | context`, retrieve real
evidence from genomics databases, score it through a causal (not associational) lens,
and return a **conditional `(position, necessity/sufficiency, context)` verdict** with a
**gated ordinal tier** as the headline, a subordinate calibrated posterior, and a
falsifiable experimental roadmap.*

> **Reconciliation status.** This brief is aligned to `DESIGN.md` and the shipped
> schema. Where an older draft said *driver/passenger/bystander*, a bare numeric
> posterior, or a single flat verdict, that has been corrected. `DESIGN.md` wins any
> remaining discrepancy. The vocabulary, enums, and invariants below match
> `src/schema.py` exactly — do not reintroduce the old ones.

---

## 0. Architecture (chosen: hybrid)

A **deterministic Python core** (retrieval + scoring + report assembly) wrapped by a
**thin LLM agent** that handles the fuzzy edges (question parsing, mechanism narration,
prose synthesis). The verdict math lives entirely in the deterministic core so results
are reproducible and testable; **the LLM never computes a score.**

```
┌─────────────────────────────────────────────────────────────┐
│  Agent layer (LLM)   — parse question · narrate · assemble    │
│                        prose. NEVER computes causal scores.   │
├─────────────────────────────────────────────────────────────┤
│  Orchestrator        — routes question-type → evidence stack, │
│                        runs connectors, calls scorer, decides │
│                        when to stop (VOI).                    │
├───────────────┬───────────────┬───────────────┬──────────────┤
│ Question      │ Evidence      │ Scoring       │ Report        │
│ Ontology      │ Connectors    │ Engine        │ Builder       │
│ (typing +     │ (per-DB, to a │ (rubric +     │ (Appraisal    │
│ evidence-stack│ common        │ gated tier +  │ obj → JSON/   │
│ registry)     │ Evidence rec) │ subord. post.)│ HTML/spider)  │
├───────────────┴───────────────┴───────────────┴──────────────┤
│  Harmonization layer — gene/variant/disease/tissue ID mapping │
│  Cache + provenance store (every record kept with source)     │
│  Validation harness — gold-standard calibration               │
└─────────────────────────────────────────────────────────────┘
```

The pure-agent and CLI variants are slices of this: the CLI is the core without the
agent layer; the pure-agent MVP is the agent calling connectors directly, deferring the
deterministic scorer. **Build the core first.**

**Stack:** Python 3.11+, `pydantic` v2 (schemas/validation — already in use), `httpx`
(async HTTP), `duckdb` + local Parquet (cache & bulk joins), `pandas`/`polars`, `pyyaml`
(registry), `scipy`/`statsmodels` (stats, MR sensitivity), `plotly` or `matplotlib`
(spider chart), `FastAPI` (optional service). Agent layer via the Claude Agent SDK / a
Cowork skill. Package manager `uv` or `poetry`. Test with `pytest` + recorded HTTP
fixtures (`vcrpy`).

---

## 1. Core data model — USE THE SHIPPED SCHEMA

**Do not invent a data model. `src/schema.py` is built, tested (26 passing), and
authoritative.** Three objects flow through the system: **Question → Evidence[] →
TargetAppraisal**. The retrieval/connector layer produces `EvidenceItem`s; the scorer
consumes them and emits a `TargetAppraisal`.

### 1.1 Question (to build — the one object not yet in schema)

The parsed question. The agent produces it from free text; a human can confirm/edit
before retrieval. Note the `context` slots must match the shipped `Context` model
(cell_type, tissue, background, ancestry, sex, disease_subtype, stage, dose, time).

```jsonc
{
  "source": {"type": "gene", "id": "ENSG00000142192", "symbol": "APP"},
  "target": {"type": "disease", "id": "MONDO:0004975", "label": "Alzheimer disease"},
  "edge_type": "causal_risk",          // regulatory | physical | genetic_risk | causal_risk | causal_effect
  "hypothesized_direction": "source_to_target",
  "context": {                          // maps 1:1 to schema.Context; may be partially null
    "cell_type": "CL:0000540", "tissue": "UBERON:0000955",
    "background": null, "ancestry": "EUR",
    "sex": null, "disease_subtype": "early-onset",
    "stage": null, "dose": null, "time": null
  }
}
```
Node types: `variant | gene | transcript | protein | pathway | cell_state | phenotype |
disease | drug`.

### 1.2 Evidence record → maps to `schema.EvidenceItem`

Every connector maps its native payload into `EvidenceItem`. **Field alignment (native
draft → shipped schema):**

| native draft field | shipped `EvidenceItem` field | note |
|---|---|---|
| `modality` | `evidence_type` (enum) | controlled vocab in `schema.EvidenceType` |
| `causal_tier` (1..5) | — (derived by scorer from `evidence_type`) | do not hand-set; the scorer assigns tier |
| `direction` | `direction` (enum `Direction`) | UP_HARMS / DOWN_PROTECTS / … / NULL |
| `carries_direction` | *implicit in `evidence_type`* | cross-sectional/co-expression types carry no direction; enforce in scorer |
| `effect {value, ci, unit, z}` | `effect: EffectSize` | `EffectSize` has value, ci_low, ci_high, units |
| `context_observed` + `context_match` | `context_match: float` on the assessment | compute vs. question `Context` |
| `provenance.*` | `source` (DOI/PMID, validated) + `provenance_group` + `record_type` | `source` MUST be DOI/PMID — schema rejects otherwise |
| `confounder_flags` | `assumptions_required` + surfaced in confounder hunt | see §5 |
| `retracted`/`replication` | drop or down-weight in scorer | invariant #6 |

**The `source` validator is strict:** a DOI (`10.…`) or `PMID:…` is required, or the
record is refused. Uncited evidence does not enter the ledger. This is deliberate — do
not relax it.

### 1.3 Verdict → USE `schema.TargetAppraisal` (NOT a hand-rolled dict)

The output is the shipped `TargetAppraisal`. Its shape — and the ways it differs from
the pre-reconciliation draft — are **mandatory**:

- **`archetype`** is the 7-way structural position label, values exactly:
  `validated_driver | associated_noncausal | displaced_signal | upstream_initiator |
  downstream_mediator | reactive_consequence | untested`.
  **There is no `passenger`.** ("Passenger" split into `downstream_mediator` (on-path,
  causal) and `reactive_consequence` (off-path, downstream).)
- **`composite`** is the gated ordinal tier — **the headline**. Values:
  `causal_driver | likely_causal | plausible | unvalidated | likely_noncausal | refuted`.
- **`inus: InusVerdict`** carries necessity × sufficiency on **separate arms**
  (`necessity`, `sufficiency` ∈ `supported/refuted/untested`), combined into a box:
  `necessary_and_sufficient | necessary_not_sufficient | sufficient_not_necessary |
  neither | undetermined`. Orthogonal to position.
- **`posterior: Optional[Posterior]`** is **subordinate**. It may be `None`. It **must
  never exceed the gated tier** (`posterior_respects_gate()`), and it renders via
  `Posterior.render()` — a **band + provenance pre-calibration, digits only once
  calibrated**. Never emit a bare float.
- **`context: Context`** is never omitted; an unscoped verdict says so.
- Plus `not_examined`, `stopped_because`, `conflicts`, `coarse_label_warning`,
  `next_experiment`, `known_limitations`.

Emit `TargetAppraisal.verdict_line()` as the one-line human summary. Ship the schema
as `/schemas/*.json` (JSON Schema draft 2020-12, via `model_json_schema()`) for
external consumers.

---

## 2. Question ontology → evidence-stack registry (the spine)

**This is the highest-value net-new artifact in this brief — it is not in DESIGN.md.**
A declarative table: for each `(source_type, target_type, edge_type)`, the ranked list
of modalities that can establish that arrow. Store as YAML so scientists can edit it.

```yaml
# registry/evidence_stacks.yaml
- match: {source: variant, target: disease, edge: genetic_risk}
  canonical_stack:
    - {modality: gwas_finemap,            tier: 4, gives_direction: true}
    - {modality: mendelian_randomization, tier: 2, gives_direction: true}
    - {modality: eqtl_coloc,              tier: 3, gives_direction: true}
    - {modality: clinvar_omim_curation,   tier: 1, gives_direction: true}
  key_confounders: [LD, population_stratification, winners_curse]

- match: {source: gene, target: gene, edge: regulatory}
  canonical_stack:
    - {modality: perturb_seq,       tier: 3, gives_direction: true}
    - {modality: crispr_ko_depmap,  tier: 3, gives_direction: true}
    - {modality: l1000_signature,   tier: 3, gives_direction: true}
    - {modality: eqtl_transacting,  tier: 4, gives_direction: true}
    - {modality: coexpression,      tier: 5, gives_direction: false}   # hypothesis only
  key_confounders: [batch, cell_type_composition, indirect_mediation]

- match: {source: disease, target: gene, edge: causal_effect}   # reverse-causation trap lives here
  canonical_stack:
    - {modality: longitudinal_omics,             tier: 4, gives_direction: true}
    - {modality: mendelian_randomization_reverse, tier: 2, gives_direction: true}
    - {modality: case_control_deg,               tier: 5, gives_direction: false}
  key_confounders: [reverse_causation, cell_type_composition, medication_effects]

- match: {source: drug, target: phenotype, edge: causal_effect}
  canonical_stack:
    - {modality: rct,                              tier: 1, gives_direction: true}
    - {modality: l1000_signature,                 tier: 3, gives_direction: true}
    - {modality: mendelian_randomization_drugtarget, tier: 2, gives_direction: true}
  key_confounders: [placebo, off_target, indication_bias]
# … one entry per supported combination; start with these four, expand.
```

The `tier` here is the **retrieval prior** on how much causal weight a modality *can*
carry for that arrow; the scorer still assigns the actual per-item tier from evidence
quality. `gives_direction: false` modalities are subject to the directionality gate
(§5.2). The orchestrator matches the parsed question to a stack entry, queries those
modalities in tier order, and stops per the VOI rule (§5).

---

## 3. Database connector catalog (verified 2025–2026 access)

Every connector implements the same interface and maps its native payload into
`schema.EvidenceItem`. **Auth reality:** only OpenGWAS (JWT) and OMIM (registered key)
are hard-gated; CLUE.io and STRING-enrichment need a free key; everything else is
keyless. Prefer bulk/cloud paths for scale where noted.

**Demo scope (from DESIGN.md): wire rows 1–5 first (Class-A, autonomous).** Rows 7–9
(the do-operator) are Phase 2; rows for Class-B cohorts are handoff-only.

| # | Source | Modality | Endpoint / access | Auth | Notes |
|---|---|---|---|---|---|
| 1 | **Open Targets Platform** | integrated / backbone | GraphQL `https://api.platform.opentargets.org/api/v4/graphql`; bulk FTP + BigQuery `open-targets-prod` | none | Genetics merged in (2024–25): L2G, fine-mapping, coloc. Backbone + benchmark. |
| 2 | **GWAS Catalog** | gwas_finemap | REST v2 `https://www.ebi.ac.uk/gwas/rest/api/v2/`; sumstats API; FTP bulk | none | Effect sizes, risk alleles, EFO traits. |
| 3 | **OpenGWAS / MR-Base** | mendelian_randomization | REST `https://api.opengwas.io/api/`; R `TwoSampleMR`/`ieugwasr`, Py `ieugwaspy` | **JWT bearer (since 05/2024)** | ~40k harmonized GWAS; two-sample MR, LD clumping. Run MR-Egger/weighted-median for pleiotropy. |
| 4 | **eQTL Catalogue** | eqtl_coloc | REST `https://www.ebi.ac.uk/eqtl/api/`; tabix FTP; SuSiE credible sets | none | Colocalization inputs across tissues/cell types. Tabix for scale. |
| 5 | **gnomAD** | constraint/plausibility gate | GraphQL `https://gnomad.broadinstitute.org/api`; buckets `gs://gcp-public-data--gnomad/` | none | v4.1/GRCh38. pLI/LOEUF constraint. ~10 req/min → buckets for bulk. |
| 6 | **ClinVar** | clinvar_omim_curation | E-utilities `.../entrez/eutils/` (`db=clinvar`); FTP XML | optional NCBI key | Variant–disease significance + review stars. |
| 7 | **DepMap** | crispr_ko_depmap | Bulk: portal + per-release Figshare DOIs; R `depmap`. Key file `CRISPRGeneEffect.csv` | none | Chronos gene-effect. **No query API — ingest + cache locally.** 25Q2. |
| 8 | **LINCS L1000** | l1000_signature | SigCom `https://maayanlab.cloud/sigcom-lincs/` (keyless); CLUE.io (key); bulk GEO GSE92742/70138 | CLUE key; SigCom none | Directional up/down perturbation signatures. |
| 9 | **scPerturb** | perturb_seq | Zenodo `https://zenodo.org/records/13350497` (h5ad) | none | ~50 harmonized single-cell perturbation datasets; E-distance effects. |
| 10 | **Europe PMC** | literature / text_mined | REST `.../europepmc/webservices/rest/`; Annotations API | none | Text-mined relations. Tag `text_mined` (lowest trust). |
| 11 | **CELLxGENE Census** | context/expression | Python `cellxgene-census` (TileDB-SOMA); S3 bucket | none | Cell-type/tissue backdrop; pin `census_version`. |
| 12 | **STRING / Reactome** | plausibility (tiebreaker) | STRING `https://version-12-0.string-db.org/api/`; Reactome ContentService | STRING key (free) | Mechanism/pathway — **plausibility axis only, never raises score alone.** |
| 13 | **OMIM / ClinGen** | gold standard (validation) | OMIM REST (key); ClinGen downloads/API | OMIM key; ClinGen none | Gene–disease validity = calibration truth set (§7). |

**Connector contract (all identical):**
```python
class BaseConnector(Protocol):
    modality: str
    def available_for(self, q: Question) -> bool: ...
    async def fetch(self, q: Question) -> list[EvidenceItem]: ...
    # maps native → schema.EvidenceItem; sets source (DOI/PMID), provenance_group,
    # direction, assumptions_required; leaves tier for the scorer to assign.
```
Ship with a shared cache (`duckdb`), a rate-limiter/backoff, and recorded fixtures
(`vcrpy`) so tests run offline.

---

## 4. Harmonization layer (silent prerequisite — build early)

Cross-DB joins fail without ID mapping; a failed join looks like "no evidence."
Normalize:
- **genes:** Ensembl ↔ HGNC (`mygene.info` or Open Targets); **variants:** GRCh38, rsID
  ↔ HGVS/SPDI;
- **disease:** MONDO/EFO (map user terms via OLS/`text2term`); **phenotype:** HPO;
  **compound:** ChEBI/ChEMBL; **tissue/cell:** Uberon/CL.
- **Coarse-label detector:** if a disease term maps to many MONDO subtypes, set
  `coarse_label_warning=True` on the appraisal and offer to stratify (the memo's
  "collection of diseases" point).

---

## 5. Scoring engine (deterministic — the trustable core)

**Per-criterion rubric, 0–3 anchors** in `scoring/rubric.yaml`, matching the 8 CSP axes
in `DESIGN.md` (A1–A4 identification, B1–B4 corroboration). Scored on **two separate
axes** — `for` and `against/confounded` — never netted until the end. The existing
`src/scoring.py` (gating + archetype classifier) is the spine; extend it, don't replace
it.

1. **Normalize effect sizes within modality** (z or rank) so an L1000 and an MR effect
   are comparable.
2. **Directionality gate (invariant #1):** an item whose `evidence_type` carries no
   direction (cross-sectional/co-expression) contributes to `strength`/`consistency`
   **only** — it can never move temporality, direction, or the driver-vs-mediator call.
3. **Tier weight:** each item's contribution ∝ its causal tier (tier-1 ≫ tier-5).
4. **Context match:** down-weight by `context_match` (wrong cell type is weaker for the
   asked context).
5. **Confounder penalty, keyed to data type** (DESIGN §"confounder hunt"): unresolved
   flags move mass to the `against` axis (e.g. untested horizontal pleiotropy caps an MR
   item's tier). Each modality has a *named* signature confounder + test — not a generic
   hunt.
6. **The gate, then the subordinate posterior** — this is the reconciled discipline, and
   it replaces the old "posterior is the output":
   - **First compute the gated ordinal tier** (`schema.Composite`) via the rules already
     in `src/scoring.py`: ceiling = strongest causal-evidence tier present; identification
     gate `tier ≤ min(A1..A4)`; bidirectional unlocks top; contradiction forces down.
     **This is the headline output.**
   - **Then, optionally, a `Posterior`:**
     `value = sigmoid( logit(prior) + Σ_i tier_i·direction_i·context_i·z_i − Σ_j penalty_j )`,
     prior from base rate (in curated set? gene constraint? network distance?), reported
     explicitly via `prior_source`. **Clamp so `value` never exceeds the tier ceiling
     (`posterior_respects_gate()` must hold).** Set `calibrated=False` until the harness
     (§7) runs; `render()` then shows a band, not a float.
7. **Conflict surfacing (invariant #5):** tier-weighted directional disagreement emits a
   `conflicts[]` entry — never averaged away.
8. **Necessity/sufficiency → `InusVerdict` (separate arms):** loss-of-function evidence
   sets the `necessity` arm; gain-of-function-in-naive-background sets the `sufficiency`
   arm. Combine via `InusVerdict.box`. The two middle boxes
   (`necessary_not_sufficient` vs `sufficient_not_necessary`) are the whole point — keep
   them distinct; each carries a different `therapeutic_note`.

**Position mapping** is the archetype classifier already in `src/scoring.py` (order
matters: mediator check before marker check). Do not re-derive it from the posterior.

**Stopping rule (VOI):** after each tier, estimate whether the best remaining modality
*could* flip the verdict given current state + its max plausible weight. If not
(marginal VOI < ε), stop and record `not_examined` + `stopped_because`. Also stop on
tier-1 conclusive or checklist-complete. **Never silently truncate.**

---

## 6. Report builder (the deliverable)

Render `TargetAppraisal` to (a) JSON, (b) a standalone HTML report, (c) an 8-axis CSP
**spider chart**. Follow the **12-section canonical order in DESIGN.md / Report Spec**
(Verdict+scope+tier; estimand five-slot `do()`; DAG with adjustment-set-in-words and
labeled collider; four-explanation checklist; evidence FOR; evidence AGAINST/nulls; CSP
profile; evidence hierarchy; databases→named-gaps with access class; roadmap; conclusions
by tier; references). **Headline is the gated tier; the posterior appears via
`render()`, subordinate.** Provenance tags (`[VERIFIED]/[RETRIEVED]/[TRAINING—verify]/
[INFERRED]`) on every quantitative claim. Use the `dataviz` skill palette for charts.

---

## 7. Validation harness (build this FIRST — critique §P5)

Before trusting any verdict:
- **Positive set:** ClinGen Definitive/Strong + OMIM monogenic pairs.
- **Negative/hard set:** curated non-associations; retracted / failed-replication claims.
- **Calibration:** bin by posterior; a 0.9 bin should be right ~90% (reliability
  diagram). **Only after this passes may `Posterior.calibrated=True` and digits show.**
- **External anchor:** genetically-supported drug targets succeed ~2× more often — the
  tool should reproduce that separation.
- **Known-answer fixtures (already built, `tests/test_known_answers.py`, 26 passing):**
  PCSK9, HDL/CETP, CRP/IL-6, APP/amyloid, tau — spanning CVD / oncology / neuro. These
  run in CI on recorded fixtures. Extend, don't rewrite.

---

## 8. Phased roadmap

**Phase 0 — skeleton (1–2 wk):** `Question` model + orchestrator; harmonization; cache;
`BaseConnector`; **Open Targets connector**; validation harness stub with ClinGen. One
question type end-to-end (`variant → disease`). Schema + fixtures already done.
**Phase 1 — causal backbone (2–4 wk):** GWAS Catalog + OpenGWAS/MR (pleiotropy tests) +
eQTL coloc + gnomAD/ClinVar gates. Extend scoring engine (gated tier + subordinate
posterior + directionality gate + INUS arms). Report builder + spider chart.
**Phase 2 — the do-operator (3–5 wk):** DepMap + L1000 + scPerturb (bulk ingest + cache).
Reversibility + necessity/sufficiency evidence. `gene → gene` and `disease → gene` types.
**Phase 3 — calibration + agent (2–3 wk):** full calibration → license the posterior's
digits; agent layer for parsing + prose; Cowork skill wrapper; VOI stopping tuned.
**Phase 4 — context depth:** CELLxGENE context matching; coarse-label stratification;
subgroup `(target, disease, subgroup)` verdicts; N-of-1 research track.

**Definition of done for v1:** given `variant/gene → disease | context`, returns a
conditional verdict — **gated tier headline**, structural position archetype, INUS box,
subordinate (uncalibrated-band) posterior — with real records from ≥4 sources, a
data-type-keyed confounder hunt, and a roadmap, and passes the ClinGen calibration check.

---

## 9. Non-negotiable invariants (encode as tests — these match `DESIGN.md` #1–8)

1. A direction-less item (cross-sectional/co-expression) never changes the
   **driver/mediator** call.
2. Plausibility / STRING / Reactome / mechanism never raise the posterior on their own.
3. Every Evidence has provenance (DOI/PMID); a claim with no queryable record is dropped,
   not scored.
4. Every Appraisal has explicit `context` scope, `prior` (on the posterior), `not_examined`,
   and `next_experiment`/roadmap.
5. Conflicting directional evidence is surfaced, never averaged.
6. Retracted / failed-replication sources cannot contribute positive weight.
7. Classification is invariant to disease area; rationales are complete without exemplars.
8. **The posterior never exceeds the gated tier (`posterior_respects_gate()`), and shows
   digits only when `calibrated=True`.**

Several already have passing tests in `tests/test_known_answers.py` (#1, #7, #8). The
rest become tests as their code lands.

---

## 10. What NOT to do (guardrails against regression)

- **Do not reintroduce `passenger`.** The vocabulary is the 7 structural archetypes.
- **Do not make the posterior the headline**, and do not emit a bare float before
  calibration. Tier is the headline; `Posterior.render()` is the only display path.
- **Do not sum dimensions.** Gate. A beautiful mechanism cannot raise the tier (the CETP
  rule). If you're writing `Σ weight·score` across dimensions, stop.
- **Do not let the LLM compute a score.** Parsing and prose only.
- **Do not hand-set `causal_tier` on evidence records.** The scorer assigns it.
- **Do not relax the `source` DOI/PMID validator.** Uncited evidence stays out.
- **Do not fake `upstream_node_carries_signal`** for the `displaced_signal` archetype —
  it needs real pathway context and is a passed-in parameter.
- **Do not invent effect sizes or PMIDs.** Curate by hand until connectors are live; the
  fixtures ship `TODO:cite` placeholders precisely so nothing invented leaks.
