# proj-CAUala 🐨

**Climbing the causal tree.** Turn *"A is associated with B"* into
*"A causes B, in context C, to this degree, with this confidence — and here is the
experiment that would prove me wrong."*

---

## What this is, and why it exists

Most of biology quietly measures **association** and then narrates it as
**causation**. That mistake is expensive — and CAUala is built to stop it.

Causality is hard to hold onto. This tool exists to help you climb as close to it
as the available evidence allows, and to be honest about how close that is. The cost
of getting it wrong is real: chasing a passenger target for a decade, giving a
patient a drug that can't help them, or building on a mechanism that doesn't hold.

**And biology breaks the standard rules for causation.** The textbook tests were
built for single-exposure epidemiology, and molecular biology hands you a
counterexample to each of them.

A tool that applies one fixed rule is confidently wrong on exactly the cases that
matter most. So CAUala doesn't: it **fits the evidence standard to the question** —
the arrow you're asking about decides which evidence can settle it — and it always
answers **conditionally** (`A → B | context`), never with a context-free yes/no.

> The deeper motivation (and why the textbook causal rules break in molecular
> biology) is in **[memo.md](memo.md)**; the reasoning framework is in
> **[CONCEPTS.md](CONCEPTS.md)**.

---

## The core idea: association ≠ causation

The whole point is that **ranking by correlation and ranking by causation
disagree** — and that gap is where expensive mistakes live. CAUala is designed to
recover the cases the field already paid to learn. It does, today, from real
evidence:

| Target → disease | Correlates with disease? | CAUala's verdict | What it really is |
|---|---|---|---|
| **PCSK9** → coronary artery disease | yes | `causal_driver` | validated driver (drugs work) |
| **HDL cholesterol** → coronary artery disease | **strongly** | `refuted` | a marker — HDL-raising drugs failed |
| **CRP** → coronary artery disease | strongly | `likely_noncausal` | the signal is one node upstream (IL-6) |
| **amyloid** → Alzheimer's | **weakly** | `likely_causal` | an early, upstream initiator |
| **tau** → Alzheimer's | strongly | `plausible` | an excellent biomarker, uncertain target |

HDL and tau **correlate beautifully but aren't drivers**; amyloid **correlates
weakly but is causal**. A tool that only ranked association would get all three
backwards. That divergence is the product.

---

## What you get back

Ask a question like *"does PCSK9 cause coronary artery disease?"* and CAUala returns
a structured, cited report:

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
commands, and the architecture are in **[IMPLEMENTATION.md](IMPLEMENTATION.md)**.

---

## How it works, in one breath

CAUala **types your question** (`source → target | context`), looks up **which kinds
of evidence can actually establish that arrow**, **queries real genomics databases**
for them (Open Targets, gnomAD, and more), **scores** what it finds through a causal
lens on separate *for* and *against* axes, and returns the verdict above. The
scoring is a **deterministic Python core** so results are reproducible and testable;
an optional LLM layer only parses questions and writes prose — **it never computes a
score.**

Three principles keep it honest:

1. **Conditional, not global.** The claim is always `A → B | context`; generalizing
   beyond the observed context is flagged, not assumed.
2. **A mechanism story can never raise the score.** A beautiful pathway is a
   tiebreaker, not evidence of causation (this is exactly how false claims *feel*
   true). The score is **gated**, not summed.
3. **Direction has to be earned.** Cross-sectional correlation carries zero
   directional credit; direction comes from genetics, time-course, or perturbation.

The full framework (Pearl's ladder + Bradford Hill, re-derived for molecular
biology, with the evidence-tier ladder) is in **[CONCEPTS.md](CONCEPTS.md)**.

---

## 📚 Documentation

Every document opens with a one-line **🧭 Role** banner, and the
**[documentation map](docs/README.md)** routes you by what you want to do. The short
version:

| I want to… | Go to |
|---|---|
| **Understand what it is and why** | [memo.md](memo.md) — the motivation (best first read) |
| **Understand the causal reasoning** | [CONCEPTS.md](CONCEPTS.md) — the framework |
| **Install & run it** (CLI + web) | [IMPLEMENTATION.md](IMPLEMENTATION.md) — the guide |
| **Host it as a website** for others | [docs/DEPLOY.md](docs/DEPLOY.md) |
| **Connect or add a database** | [docs/CONNECTORS.md](docs/CONNECTORS.md) |
| **Read the engineering spec** | [build-brief.md](build-brief.md) |
| **See the report format & rubric** | [docs/Causal_Evidence_Report_Spec.md](docs/Causal_Evidence_Report_Spec.md) |
| **See the reasoning stress-test** | [docs/CAUala-critique.md](docs/CAUala-critique.md) |
| **Browse everything** | [docs/README.md](docs/README.md) — the full map |

---

## Repository layout

| Path | What's there |
|---|---|
| `src/` | The deterministic core (`schema`, `scoring`, `scoring_engine`), `connectors/`, `orchestrator`, `report`, `provenance`, `cli`, `webapp`. |
| `registry/` · `scoring/` | Editable YAML: the evidence-stack registry, the curated evidence, the scoring rubric. |
| `tests/` | The 26 known-answer tests + pipeline, web, and opt-in live tests. |
| `reports/` | Generated sample reports (example outputs, not documentation). |
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
