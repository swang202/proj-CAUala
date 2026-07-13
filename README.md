# proj-CAUala 🐨

**Climbing the causal tree.** Turn *"A is associated with B"* into
*"A causes B, in context C, to this degree, with this confidence — and here is the
experiment that would prove me wrong."*

---

## What this is, and why it exists

Most of biology quietly measures **association** and then narrates it as
**causation**. That mistake is expensive, and I built CAUala to make it harder to
make.

Causality is hard to hold onto. I think the honest goal is not certainty but to
climb as close to it as the evidence allows — and to say plainly how close that is.
The cost of getting it wrong is real: chasing a passenger target for a decade,
giving a patient a drug that cannot help them, or building on a mechanism that does
not hold.

And biology breaks the textbook rules for causation, which were written for
single-exposure epidemiology. For example, the same gene can be causal on one
genetic background and neutral on another, and a knockout can look silent only
because a paralog quietly compensates. A tool that applies one fixed rule is
confidently wrong on exactly the cases that matter most. So CAUala does not: it
**fits the evidence standard to the question** — the arrow you are asking about
decides which evidence can settle it — and it always answers **conditionally**
(`A → B | context`), never with a context-free yes or no.

> The deeper motivation (and why the textbook causal rules break in molecular
> biology) is in **[memo.md](memo.md)**; the reasoning framework is in
> **[CONCEPTS.md](CONCEPTS.md)**.

---

## The core idea: association ≠ causation

The whole point is that ranking by correlation and ranking by causation disagree,
and that gap is where the expensive mistakes live. The cases below are ones the
field has already paid to learn, and CAUala recovers each:

| Target → disease | Correlates with disease? | CAUala's verdict | What it really is |
|---|---|---|---|
| **PCSK9** → coronary artery disease | yes | `causal_driver` | validated driver (drugs work) |
| **HDL cholesterol** → coronary artery disease | **strongly** | `refuted` | a marker — HDL-raising drugs failed |
| **amyloid** → Alzheimer's | **weakly** | `likely_causal` | an early, upstream initiator |
| **tau** → Alzheimer's | strongly | `plausible` | an excellent biomarker, uncertain target |
| **LRRK2** → Parkinson's | moderately | `likely_causal` | a genetic driver — scored **live** from GWAS + ClinVar |

HDL and tau **correlate beautifully but are not drivers**; amyloid **correlates
weakly but is causal**; and LRRK2 is a bona fide genetic driver, recovered from live
databases with no curated help. A tool that ranked by association alone would get
these backwards, and that disagreement is the product.

**How it does this, in brief.** CAUala types your question into
`source → target | context`, looks up which kinds of evidence can actually establish
that arrow, and **queries real genomics databases for them — Open Targets and gnomAD
today, live over the network** — with more sources being added. It then scores what
it finds through a causal lens, on separate for-and-against axes, and it *gates*
rather than sums: association and mechanism alone are capped, a beautiful pathway can
never buy a causal score, and direction has to come from genetics, time, or
perturbation, never from cross-sectional correlation. The scoring is a deterministic
Python core, so results are reproducible; an optional language-model layer only
parses the question and writes prose, and it never computes a score.

One honest caveat: live coverage is still growing. Open Targets' integrated score
and gnomAD constraint carry no direction; the directional signal comes from the Open
Targets **genetics** and **variant** queries (GWAS credible sets, rare-variant
burden, ClinVar) — which is exactly what earns LRRK2 its verdict. For a gene with
little of that, the tool honestly says "unvalidated" rather than guessing, and the
CVD/AD verdicts above also lean on hand-curated directional evidence. The machinery
runs end-to-end on real data; more live sources are being added.

---

## What you get back

Ask *"does PCSK9 cause coronary artery disease?"* and you get back a structured,
cited report — not a single number:

- a **headline verdict tier** (`causal_driver` → `likely_causal` → `plausible` →
  `unvalidated` → `likely_noncausal` → `refuted`);
- a **structural position** (validated driver, associated-but-not-causal, upstream
  initiator, downstream mediator, …);
- **necessity × sufficiency** (is the target required, enough, both, or neither?);
- the **context** the verdict is scoped to;
- a **confidence band** (subordinate to the tier, and honest that it's uncalibrated);
- the **evidence for and against**, each **cited and tagged for validation**;
- an **8-axis spider chart** of causal strength, and the **next experiment** that
  would move the verdict.

Every figure pulled from a live database is tagged `[RETRIEVED]` (verify in-source);
nothing is presented as a checked fact that hasn't been checked.

---

## Try it in 30 seconds

**A hosted website is on the way** — I am setting it up on Render right now, so soon
you will be able to open a link and use CAUala with no install at all. In the
meantime, it runs locally in a few commands:

```bash
# one-time setup
uv venv --python python3.11 .venv
uv pip install --python .venv -e '.[web]'      # or: pip install -r requirements.txt

# 1) the web app — a browser form, live progress, a rendered report
.venv/bin/python -m src.cli serve              # then open http://127.0.0.1:8000

# 2) or the command line — just two words
.venv/bin/python -m src.cli appraise PCSK9 "coronary artery disease"

# offline (curated evidence, no network):  add  --offline
```

The web app is the easiest entry point for non-technical users: type a gene and a
disease, watch it stream *what it's looking at right now* (which databases it's
querying, what it found), then read the report in the page. Full install, all CLI
commands, and the architecture are in **[IMPLEMENTATION.md](docs/IMPLEMENTATION.md)**.

---

## 📚 Documentation

Every document opens with a one-line **🧭 Role** banner, and the
**[documentation map](docs/README.md)** routes you by what you want to do. The short
version:

| I want to… | Go to |
|---|---|
| **Understand what it is and why** | [memo.md](memo.md) — the motivation (best first read) |
| **Understand the causal reasoning** | [CONCEPTS.md](CONCEPTS.md) — the framework |
| **Install & run it** (CLI + web) | [IMPLEMENTATION.md](docs/IMPLEMENTATION.md) — the guide |
| **Host it as a website** for others | [docs/DEPLOY.md](docs/DEPLOY.md) |
| **Connect or add a database** | [docs/CONNECTORS.md](docs/CONNECTORS.md) |
| **Read the engineering spec** | [build-brief.md](docs/build-brief.md) |
| **See the report format & rubric** | [docs/Causal_Evidence_Report_Spec.md](docs/Causal_Evidence_Report_Spec.md) |
| **See the reasoning stress-test** | [docs/CAUala-critique.md](docs/CAUala-critique.md) |
| **Browse everything** | [docs/README.md](docs/README.md) — the full map |

---

## Repository layout

| Path | What's there |
|---|---|
| `src/` | The deterministic core (`schema`, `scoring`, `scoring_engine`, `exemplars`), entity `resolve`, `harmonization`, `orchestrator`, `report`, `provenance`, `validation`, `cli`, `webapp`. |
| `src/connectors/` | The connector contract + the live sources (Open Targets, its genetics & variant queries, gnomAD) and the offline `fixtures` backbone. |
| `registry/` · `scoring/` | Editable YAML: the evidence-stack registry, the curated evidence, the scoring rubric. |
| `tests/` | The 26 known-answer tests + pipeline, web, and opt-in live tests. |
| `docs/` | The documentation hub and guides — start at [docs/README.md](docs/README.md). |
| `reports/`, `schemas/` | **Generated** — reports via `cauala appraise --out`, schemas via `cauala export-schemas`. Git-ignored, not committed. |
| `Dockerfile`, `render.yaml`, `fly.toml`, `Procfile`, `deploy/` | Hosting configs — see [docs/DEPLOY.md](docs/DEPLOY.md). |

---

## Status

**Built and running.** The deterministic core, live database connectors
(Open Targets + gnomAD), the report builder, a CLI, and a browser web app are
implemented and tested — 26 known-answer tests plus pipeline and web tests passing,
and the validation harness reproduces the association-vs-causation separation above.

**Honest limits (worth knowing up front):** the confidence posterior is
uncalibrated (shown as a band, never a bare number, until a gold-standard
calibration runs); the curated example evidence still carries placeholder citations
(tagged `[UNVERIFIED]`) pending in-source verification; and live database numbers
are real but tagged `[RETRIEVED]` until you check them at the source. Verdicts are a
decision aid, not a substitute for reading the primary evidence.
