# proj-CAUala — implementation guide

What was built against `build-brief.md`, how to run it, and where each piece of the
brief lives in code. The architecture is the brief's **hybrid**: a deterministic
Python core (retrieval + scoring + report), with the agent layer as a thin,
optional front-end that only parses free text into a `Question` and narrates —
**the LLM never computes a score.**

## Quick start

```bash
uv venv --python python3.11 .venv
uv pip install --python .venv -e .          # or: pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -q        # 37 passing
.venv/bin/python -m src.cli demo            # known-answer table
.venv/bin/python -m src.cli validate        # calibration/separation harness
.venv/bin/python -m src.cli appraise \
    --source PCSK9 --target "coronary artery disease" --edge causal_risk --format md
.venv/bin/python -m src.cli export-schemas  # JSON Schemas -> ./schemas
```

`appraise` also takes `--format json|html`, `--out FILE`, context flags
(`--ancestry`, `--tissue`, `--cell-type`, `--disease-subtype`, `--stage`, `--sex`),
and `--online` (enables the live Open Targets connector; offline it degrades to a
named gap).

## Module map

| Brief section | File | What it does |
|---|---|---|
| §1 data model (shipped) | `src/schema.py` | The authoritative schema, moved into the package unchanged. |
| §1.1 Question | `src/question.py` | The one net-new core object: typed `source → target \| context`. |
| §2 evidence-stack registry | `registry/evidence_stacks.yaml` | Per `(source,target,edge)` ranked modality stack + key confounders. |
| §3 connectors | `src/connectors/` | `base.py` contract + cache; `fixtures.py` offline backbone; `opentargets.py` live GraphQL. |
| §4 harmonization | `src/harmonization.py` | ID resolution + coarse-label detector (never fabricates an id). |
| §5 scoring engine | `src/scoring.py`, `src/scoring_engine.py` | The gate + archetype classifier; CSP, INUS arms, subordinate posterior, VOI. |
| §5 rubric | `scoring/rubric.yaml` | 8-axis CSP anchors, identification gate, per-type axis priors, named confounders. |
| §6 report builder | `src/report.py` | JSON / Markdown / HTML in the 12-section order + inline-SVG spider chart. |
| §7 validation harness | `src/validation.py`, `tests/test_pipeline.py` | Known-answer recovery + association-vs-causal separation. |
| orchestration | `src/orchestrator.py` | Routes question → stack → connectors → scorer → appraisal, with VOI + gaps. |
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
- **Live connectors**: only Open Targets is wired for `--online`; the other rows in
  the §3 catalog have registry entries and a uniform contract but are not yet
  implemented. The offline FixtureConnector is the reproducible backbone the demo
  and tests run against (recorded-fixture equivalent).

## Phase status vs the brief roadmap

Phase 0 (skeleton: Question, harmonization, cache, BaseConnector, one
question-type end-to-end) and the Phase-1 scoring backbone (gated tier +
subordinate posterior + directionality gate + INUS arms + report + spider chart +
validation harness) are implemented and tested. Phase 2 (DepMap/L1000/scPerturb
do-operator connectors), Phase 3 (full calibration to license posterior digits +
the agent layer) and Phase 4 (CELLxGENE context depth) are stubbed at the contract
/ registry level and left for follow-on.
