# proj-CAUala — implementation guide

> 🧭 **Use & build — run it + architecture.** What shipped, how to run it (CLI + web + tests), and where each piece lives. New to the project? Start at [memo.md](../memo.md). Full map: **[docs/README.md](README.md)**.

What was built against `build-brief.md`, how to run it, and where each piece of the
brief lives in code. The architecture is the brief's **hybrid**: a deterministic
Python core (retrieval + scoring + report), with the agent layer as a thin,
optional front-end that only parses free text into a `Question` and narrates —
**the LLM never computes a score.**

## Quick start

```bash
uv venv --python python3.11 .venv
uv pip install --python .venv -e .          # or: pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -q        # 37 passing (+3 opt-in live, skipped)

# the web app — a browser form, live progress, rendered report (easiest for non-CLI users):
.venv/bin/python -m src.cli serve           # then open http://127.0.0.1:8000

# the easy CLI path — two words, online by default (live Open Targets + gnomAD):
.venv/bin/python -m src.cli appraise PCSK9 "coronary artery disease"

.venv/bin/python -m src.cli demo            # known-answer table (offline, reproducible)
.venv/bin/python -m src.cli validate        # calibration/separation harness (offline)
.venv/bin/python -m src.cli export-schemas  # JSON Schemas -> ./schemas
```

The **web app** (`src/webapp.py`, FastAPI) is the friendliest entry point: type a
gene and a disease, watch it stream *what it's looking at right now* (harmonize →
query each database → tier → gate → classify) via Server-Sent Events, then read
the rendered, cited, validation-flagged report in the page. It reuses
`Orchestrator.appraise_events`, so the browser sees the exact CLI pipeline.
Install the web extra with `uv pip install --python .venv -e '.[web]'`.

**Hosting it as a public website:** the app reads `$PORT`/`$HOST`, has a
`/healthz` check, CORS on the JSON API, and a concurrency cap. Ship-ready configs
are in the repo root — `Dockerfile`, `render.yaml`, `Procfile`, `fly.toml`, and a
Hugging Face Space template — with step-by-step instructions for each host in
[`docs/DEPLOY.md`](DEPLOY.md). Note: it needs a Python-capable host (it runs
server-side), so a pure static host like GitHub Pages will not work; Hugging Face
Spaces or Render are the easiest free options.

`appraise` is **online by default** — it queries live databases and every figure
is cited to its source and tagged `[RETRIEVED]` (verify in-source) or `[UNVERIFIED]`
(curated placeholder). Pass `--offline` to use only curated fixtures. It also takes
`--format json|html`, `--out FILE`, and context flags (`--ancestry`, `--tissue`,
`--cell-type`, `--disease-subtype`, `--stage`, `--sex`). See
[`docs/CONNECTORS.md`](CONNECTORS.md) for the data-source list and how to add more.

## Module map

| Brief section | File | What it does |
|---|---|---|
| §1 data model (shipped) | `src/schema.py` | The authoritative schema, moved into the package unchanged. |
| §1.1 Question | `src/question.py` | The one net-new core object: typed `source → target \| context`. |
| §2 evidence-stack registry | `registry/evidence_stacks.yaml` | Per `(source,target,edge)` ranked modality stack + key confounders. |
| §3 connectors | `src/connectors/` | `base.py` contract + cache; `fixtures.py` offline backbone; live: `opentargets.py` (integrated score), `opentargets_genetics.py` (directional GWAS/burden/ClinVar), `opentargets_variant.py` (variant-level evidence), `gnomad.py` (constraint gate). |
| §4 harmonization | `src/harmonization.py` | Offline ID table + coarse-label detector; delegates online resolution to the resolver. Never fabricates an id. |
| entity resolution | `src/resolve.py` | Type-constrained universal search + confidence gate + candidates; disease-abbreviation aliases; variant resolution (protein change → rsID via Ensembl → OT variant). |
| §5 scoring engine | `src/scoring.py`, `src/scoring_engine.py` | The gate + archetype classifier; CSP, INUS arms, subordinate posterior, VOI. |
| §5 exemplars / rubric | `src/exemplars.py`, `scoring/rubric.yaml` | Disease-area-keyed archetype illustrations; 8-axis CSP anchors, identification gate, per-type axis priors, named confounders. |
| §6 report builder | `src/report.py` | JSON / Markdown / HTML (12-section order) + inline-SVG spider chart + dimension bars. |
| §7 validation harness | `src/validation.py`, `tests/test_pipeline.py` | Known-answer recovery + association-vs-causal separation. |
| orchestration | `src/orchestrator.py` | Routes question → resolve → stack → connectors → scorer → appraisal, with VOI + gaps; `appraise_events` streams progress. |
| provenance & citation | `src/provenance.py` | Per-figure datasource citation + `[RETRIEVED]`/`[UNVERIFIED]` validation status. |
| web app + CLI | `src/webapp.py`, `src/cli.py` | FastAPI form + SSE stream + disambiguation picker + `/resolve` + JSON API; CLI (`appraise`, `serve`, `demo`, `validate`, `export-schemas`). |
| schema export | `src/export_schemas.py` | `model_json_schema()` → `schemas/*.json` (draft 2020-12). |

## How the discipline from the brief is enforced

- **Gate, never sum** (`scoring.apply_gates`): association + mechanism cap at
  `unvalidated`; a strong mechanism cannot lift the tier (the CETP rule, locked by
  `test_strong_mechanism_cannot_rescue_hdl`).
- **Directionality gate** (invariant #1): direction-less designs (cross-sectional,
  co-expression, biochemical pathway) cannot raise a causal dimension above `weak`
  and contribute 0 to the posterior (`scoring_engine.DIRECTIONLESS_TYPES`).
- **Contradiction forces down, never averaged** (invariant #5): a failed
  intervention → `refuted`; conflicts are emitted in `conflicts[]`.
- **Posterior is subordinate & gated** (invariant #8): `compute_posterior` clamps
  under the tier ceiling and ships `calibrated=False`, so `Posterior.render()`
  shows a band, never a bare float, until `validate` licenses digits.
- **Provenance required** (invariant #3): the schema's DOI/PMID validator is
  untouched; uncited evidence cannot enter the ledger.
- **Structural, disease-agnostic archetypes** (invariant #7): `disease_area` only
  selects an exemplar and can never change the archetype; rationales are complete
  without the exemplar (`test_rationale_is_complete_without_exemplar`).

## Known-answer results (offline, curated evidence)

| target | tier (headline) | position | INUS |
|---|---|---|---|
| PCSK9 | `causal_driver` | `validated_driver` | necessary_and_sufficient |
| HDL-C | `refuted` | `associated_noncausal` | undetermined |
| CRP | `likely_noncausal` | `displaced_signal` | undetermined |
| APP/amyloid | `likely_causal` | `upstream_initiator` | necessary_and_sufficient |
| tau | `plausible` | `downstream_mediator` | undetermined |

The association-strong set `{HDL-C, CRP, tau}` and the causal-strong set
`{PCSK9, APP/amyloid}` are disjoint — that gap is the product.

## Honest notes / deliberate scoping

- **DESIGN.md** is referenced by the brief as the arbiter but is not present in the
  repo. The build was reconciled against the brief + `src/schema.py` +
  `tests/test_known_answers.py` + `docs/` (Report Spec, Data Catalog, critique),
  which are mutually consistent. If DESIGN.md later appears and disagrees, it wins.
- **Curated evidence** (`registry/curated_evidence.yaml`) carries the same
  `TODO:cite` placeholder discipline as the test fixtures. The *structure* of each
  case is the known answer; the citations must be verified in-source before use.
  Nothing invented is presented as verified — provenance tags in reports read
  `[RETRIEVED]` / `[unverified]` accordingly.
- **amyloid INUS = necessary_and_sufficient** reflects the autosomal-dominant
  evidence in the fixture (a penetrant gain-of-function mutation is sufficiency
  evidence, a protective allele is necessity evidence). The memo's textbook
  "necessary-not-sufficient / INUS" framing is the *sporadic-AD* reading; feeding
  sporadic-cohort evidence (LOF reduces but does not abolish) would move the arm to
  `sufficiency=refuted`. This is the conditional, context-dependent behaviour the
  tool is designed to expose, not a bug.
- **Live connectors**: four keyless live sources are wired and working (`--online`,
  the default): **Open Targets** integrated score, **Open Targets genetics**
  (directional GWAS credible-sets / rare-variant burden / ClinVar), **Open Targets
  variant** (variant-level disease evidence), and **gnomAD** constraint. Entity
  resolution is universal via `src/resolve.py` (type-constrained Open Targets
  `search` + a small disease-abbreviation alias layer; garbage rejected, ambiguous
  handed to a picker). Protein-change **variants are first-class** (`LRRK2 G2019S` →
  rs34637584 via Ensembl → OT variant → its own disease evidence). Other §3 catalog
  sources (DepMap, L1000, scPerturb, OpenGWAS-MR, …) have registry entries and a
  uniform contract but are not yet implemented — see
  [`docs/CONNECTORS.md`](CONNECTORS.md) for the recipe and auth table. The
  offline FixtureConnector remains the reproducible backbone for the demo and tests.
- **Generated outputs are not version-controlled.** `schemas/` (`cauala
  export-schemas`) and `reports/` (`cauala appraise --out …`) are git-ignored;
  regenerate them from the CLI rather than expecting them in a fresh clone.

## Phase status vs the brief roadmap

Phase 0 (skeleton: Question, harmonization, cache, BaseConnector, one
question-type end-to-end) and the Phase-1 scoring backbone (gated tier +
subordinate posterior + directionality gate + INUS arms + report + spider chart +
validation harness) are implemented and tested. Phase 2 (DepMap/L1000/scPerturb
do-operator connectors), Phase 3 (full calibration to license posterior digits +
the agent layer) and Phase 4 (CELLxGENE context depth) are stubbed at the contract
/ registry level and left for follow-on.
