# CAUala — Project & Claude Usage

> **Note to self before submitting:** the "products" section below reflects how Claude was used in this build. Tick / adjust the exact product names to match what you actually signed in to (Claude Code and Claude.ai chat are certain; add **Claude Science** only if you used it for the literature survey). Everything else is grounded in the repo.

---

## Project description

**CAUala — climbing the causal tree.** CAUala turns *"A is associated with B"* into
*"A causes B, in context C, to this degree, with this confidence — and here is the experiment that would prove me wrong."*

Most of biology measures **association** and then narrates it as **causation**. That slip is expensive — a decade chasing a passenger target, or a drug given to a patient it cannot help. CAUala is a causal-evidence appraisal engine for molecular biology that makes the mistake harder to make.

You ask a causal question — *does A cause B?* — where A and B are any two typed biological things (variant, gene, protein, pathway, cell state, phenotype, disease, or drug). CAUala:

1. **Types the question** into `source → target | context`, and looks up which *kinds* of evidence can actually establish that specific arrow (the evidence-stack registry).
2. **Queries real genomics databases live over the network** — Open Targets (integrated score), Open Targets genetics (GWAS credible sets, rare-variant burden, ClinVar), Open Targets variant-level evidence, and gnomAD (constraint).
3. **Scores what it finds through a causal lens** with a deterministic Python core that *gates* rather than sums: association and mechanism alone are capped, a beautiful pathway can never buy a causal score, and direction has to come from genetics, time, or perturbation — never from cross-sectional correlation.
4. **Returns a structured, cited report:** a headline verdict tier (`causal_driver → likely_causal → plausible → unvalidated → likely_noncausal → refuted`), a structural position, necessity × sufficiency (INUS), the context the verdict is scoped to, an honest confidence *band*, the evidence for and against (each cited and validation-tagged), an 8-axis spider chart, and the single next experiment that would move the verdict.

**Why it's not just a smarter search.** Ranking by correlation and ranking by causation *disagree*, and that gap is where the expensive mistakes live. CAUala recovers cases the field already paid to learn: **HDL cholesterol** correlates strongly with heart disease but is **refuted** (HDL-raising drugs failed); **amyloid** correlates weakly with Alzheimer's but is **likely causal**; **LRRK2** is scored **likely causal** for Parkinson's *live, from human genetics alone*, with no curated help. A tool that ranked by association would get these backwards.

**What shipped:** a deterministic reasoning core (schema, gated scoring engine, INUS classifier, report builder with inline SVG spider chart), four working keyless live database connectors, universal entity resolution (including protein-change variants like `LRRK2 G2019S` → rsID → variant evidence), a CLI, a FastAPI web app with live Server-Sent-Events progress, 26 known-answer tests plus pipeline and web tests, and a public deployment at **cauala.onrender.com**. An optional language-model layer only parses free text and writes prose — **it never computes a score**, so every verdict is reproducible.

---

## How I used Claude

Claude wasn't a code-autocomplete on the side — it was the collaborator across the whole arc: **shaping the science, stress-testing the reasoning, and building the entire system.**

### Which products

| Product | How it was used | Where it mattered most |
|---|---|---|
| **Claude Code** | Built the entire codebase end to end — schema, gated scoring engine, INUS classifier, four live database connectors, entity resolver, report builder, CLI, FastAPI web app, the full test suite, and the Render deployment. Iterated in tight loops: write a connector, run the known-answer tests, watch the association-vs-causation separation hold or break, fix, repeat. | **Implementation.** This is where the design became a running, tested, deployed system. |
| **Claude (chat / claude.ai)** | Two distinct research jobs: (1) **surveying how the field separates association from causation** — Bradford Hill, Pearl's ladder, potential outcomes, Mendelian randomization, INUS factors — and re-deriving those rules for molecular biology; and (2) **using Claude as a test subject** — I fed it a range of causal questions and watched *where a general LLM falls short*, which directly defined CAUala's design. | **Problem-framing and design.** The three weaknesses I found became CAUala's three core commitments. |
| **Claude Science** *(if used)* | Deep literature grounding for the causal framework and the disease exemplars (PCSK9, HDL/CETP, amyloid, tau, LRRK2). | *Add only if you actually used it — otherwise fold this into the chat row above.* |

### Where Claude mattered most in the workflow

**1. It defined the design by failing usefully.** Before writing code, I fed Claude a spread of causal questions — *does gene A raise gene B's expression? does a mutation cause a disease? does a disease change a gene's expression?* — plus deliberately hard real pairs (a cancer gene affecting neurodegeneration; a risk gene with a protective effect). Claude's answers were consistent and its data-gap notes were genuinely useful, but three weaknesses stood out, and **each became a pillar of CAUala:**
   - *Citations were the biggest liability* — the decisive thing (a raw DEG matrix, a CRISPR readout, a human effect size) often isn't in the prose at all → so evidence in CAUala is a **structured record with provenance**, and it prefers databases over abstracts.
   - *Directionality was under-used* — cross-sectional co-expression carries near-zero directional information → so CAUala has a hard **directionality gate**: direction must come from genetics, time, or perturbation.
   - *Scoring was impressionistic* → so CAUala has a **fixed, gated rubric** with separate for/against axes and an explicit base-rate prior.

   This is written up in the project memo — the design is, quite literally, "the fixes for where Claude fell short."

**2. It stress-tested the reasoning before any code was written.** I had Claude hunt for loopholes in the causal logic — the cases where textbook criteria break in biology (non-monotone dose–response, sign-flipping variants, paralog compensation masking necessity, feedback loops, thresholds). Those counterexamples are what forced the *conditional* `A → B | context` framing and the question-type-specific weighting, instead of one fixed algorithm. (Captured in `docs/CAUala-critique.md`, "loopholes found and closed before any code.")

**3. It built and hardened the system.** In Claude Code, the invariants from the design became enforced, tested code: *gate-never-sum* (a strong mechanism cannot rescue HDL — locked by a test), the *directionality gate*, *contradiction forces the tier down*, the *subordinate, uncalibrated posterior that renders as a band*, and *provenance-required* (uncited evidence can't enter the ledger). The known-answer suite and the live connectors were both built and debugged with Claude in the loop, right through to the public deployment.

**The honest one-liner:** Claude was the reason CAUala is disciplined rather than impressionistic. I used it first to find where confident causal reasoning goes wrong, then to build a tool that refuses to make those same mistakes — and to keep it reproducible by making sure the language model narrates but **never scores.**

---

## Try it

- **Live:** [cauala.onrender.com](https://cauala.onrender.com) — type a gene and a disease, watch it query real databases, read the cited report.
- **Locally:**
  ```bash
  uv venv --python python3.11 .venv
  uv pip install --python .venv -e '.[web]'
  .venv/bin/python -m src.cli demo                                  # the known-answer reveal (offline, instant)
  .venv/bin/python -m src.cli appraise LRRK2 "Parkinson disease"    # live, from real databases
  .venv/bin/python -m src.cli serve                                 # the web app at http://127.0.0.1:8000
  ```
