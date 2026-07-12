# 🐨 CAUala documentation — start here

Every document in this repo, organized by **what you want to do**. If you're not
sure where to begin, follow the newcomer reading order at the bottom.

Each doc carries a one-line **🧭 Role** banner at its top, so opening any file tells
you immediately what it is and who it's for.

---

## Pick your path

| I want to… | Go to |
|---|---|
| **Just get an answer** — type a gene + disease, no install | The hosted site (ask the maintainer for the URL) or run the web app: [Guide → Quick start](../IMPLEMENTATION.md) |
| **Run it on my machine** (CLI or local web app) | [Guide (IMPLEMENTATION.md)](../IMPLEMENTATION.md) |
| **Understand what it claims & the science** | [memo.md](../memo.md) → [CONCEPTS.md](../CONCEPTS.md) |
| **Host it as a website for others** | [DEPLOY.md](DEPLOY.md) |
| **Connect or add a database** | [CONNECTORS.md](CONNECTORS.md) |
| **Read the engineering spec / extend it** | [build-brief.md](../build-brief.md) + [Guide](../IMPLEMENTATION.md) |

---

## All documents by role

### 🚀 Use & run
| Document | Role |
|---|---|
| [README.md](../README.md) | **Front door** — what CAUala is, in one page. |
| [IMPLEMENTATION.md](../IMPLEMENTATION.md) | **The guide** — install, run (CLI + web), and the module-by-module map of what was built. |
| [DEPLOY.md](DEPLOY.md) | **Host it** — put CAUala on a public URL (Hugging Face Spaces, Render, Docker, …). |

### 🧠 Understand (the science & design)
| Document | Role |
|---|---|
| [memo.md](../memo.md) | **Why it exists** — the problem, and why generic causal rules break in biology. *Best first read.* |
| [CONCEPTS.md](../CONCEPTS.md) | **The framework** — Bradford Hill + Pearl, re-derived for molecular biology. |
| [CAUala-critique.md](CAUala-critique.md) | **The stress-test** — loopholes in the logic, found and closed before any code. |

### 🔧 Build & extend
| Document | Role |
|---|---|
| [build-brief.md](../build-brief.md) | **The engineering spec** the tool was built to (architecture, schema, invariants). |
| [CONNECTORS.md](CONNECTORS.md) | **Data sources** — connect live databases and add new connectors (~40 lines each). |

### 📚 Reference
| Document | Role |
|---|---|
| [Causal_Evidence_Report_Spec.md](Causal_Evidence_Report_Spec.md) | The report house style — 12-section format + the 8-axis CSP rubric. |
| [Causal_Data_Source_Catalog.md](Causal_Data_Source_Catalog.md) | Catalog of genomics databases and how the tool reaches each. |

---

## The code, at a glance

| Path | What's there |
|---|---|
| `src/` | The deterministic core (`schema`, `scoring`, `scoring_engine`), `connectors/`, `orchestrator`, `report`, `provenance`, `cli`, `webapp`. |
| `registry/` | Editable YAML: the evidence-stack registry + the curated offline evidence. |
| `scoring/` | Editable YAML: the CSP scoring rubric. |
| `tests/` | The 26 known-answer tests + pipeline, web, and opt-in live tests. |
| `reports/` | **Generated sample outputs** (example reports — not documentation). |
| `Dockerfile`, `render.yaml`, `Procfile`, `fly.toml`, `deploy/` | Hosting configs — see [DEPLOY.md](DEPLOY.md). |

The full module-by-module map lives in the [guide](../IMPLEMENTATION.md).

---

## Newcomer reading order

1. [memo.md](../memo.md) — *why* this exists (~5 min).
2. [README.md](../README.md) — *what* it does.
3. [CONCEPTS.md](../CONCEPTS.md) — *how* the causal reasoning is shaped.
4. [IMPLEMENTATION.md](../IMPLEMENTATION.md) — run it, and see how the pieces fit.

Going deeper (developers): [CAUala-critique.md](CAUala-critique.md) → [build-brief.md](../build-brief.md) → [CONNECTORS.md](CONNECTORS.md) → the reference specs.
