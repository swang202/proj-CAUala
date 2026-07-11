# proj-CAUala 🐨 — Climbing the Causal Tree

> *Correlation is a hint. Causation is the climb.*

A small, dependency-light toolkit for a question that comes up constantly in
biology: **is this association real causation, or just correlation?** Two genes
rise and fall together — but does one *drive* the other, or do they merely share
a hidden common cause? `causala` gives you the tools to tell the difference, and
a demo that makes the distinction vivid.

It has three layers, each stricter than the last:

| Layer | Question it answers | Method |
|-------|--------------------|--------|
| **Correlation matrix** | "Do they move together?" | Pearson / partial correlation |
| **Causality matrix** | "Does one *cause* the other, and how strongly?" | PC algorithm + effect estimation |
| **Causal Tree** | "For *whom* does an intervention actually work?" | Honest heterogeneous-effect tree |

---

## The core idea in one picture

A signalling cascade `Ligand → Receptor → Kinase → TF → {GeneA, GeneB}`.
`GeneA` and `GeneB` share `TF` as a common cause, so they are strongly
**correlated** — yet there is **no** causal link between them.

```
correlation(GeneA, GeneB)      = +0.85   ← looks real, but it's the confounder talking
partial correlation | rest     = -0.02   ← the confound is removed
causality matrix edge          =  0.00   ← the PC algorithm correctly refuses the edge
```

Same data, two very different stories. That is the whole project.

---

## Install

```bash
pip install -e .          # core: numpy, scipy, pandas
pip install -e ".[dev]"   # adds matplotlib, scikit-learn, pytest for the demo & tests
```

## Quickstart

```python
from causala import (
    gene_regulatory_network, correlation_matrix, causal_discovery,
    CausalTree, treatment_response,
)

# 1. Simulate biology with a KNOWN causal graph
ds = gene_regulatory_network(n_samples=3000)

# 2. Correlation is fooled by the shared cause...
correlation_matrix(ds.data).loc["GeneA", "GeneB"]        # ~ +0.85

# 3. ...but the causality matrix is not
graph = causal_discovery(ds.data, alpha=0.01)
graph.causality_matrix().loc["GeneA", "GeneB"]           # 0.0
graph.directed_edges()   # [('Kinase','TF',1.18), ('TF','GeneA',1.0), ...]

# 4. Heterogeneous effects: who does the drug help?
df, t, y, cov = treatment_response(n_samples=5000)
tree = CausalTree(max_depth=3).fit(df[cov].values, df[t].values, df[y].values)
tree.predict(df[cov].values)   # per-patient causal effect (CATE)
```

## Run the demo

```bash
python examples/demo.py
```

Prints the full correlation-vs-causation walkthrough and writes two figures to
`examples/figures/`. Then open **`demo/index.html`** — an interactive page where
the koala climbs the causal tree, the matrices flip live, and every number is
the real output of the package (no hand-tuning).

---

## What's inside

```
src/causala/
  datasets.py       synthetic biology with ground-truth causal graphs (linear SEMs)
  ci_tests.py       (conditional) independence tests — Fisher-Z / partial correlation
  causal_matrix.py  correlation, partial correlation, and the PC algorithm
  causal_tree.py    honest Causal Tree for heterogeneous treatment effects
  metrics.py        graph-recovery scores (precision/recall, structural Hamming distance)
tests/              20 tests pinning down the science
examples/demo.py    end-to-end walkthrough + figures
demo/index.html     the interactive koala demo 🐨
```

### The methods, briefly

- **PC algorithm** (Spirtes–Glymour). Start from a fully connected graph, delete
  an edge whenever the two variables become independent given some conditioning
  set, then orient edges using v-structures and Meek's rules. The result is a
  directed **causality matrix** of estimated effects rather than a symmetric
  correlation matrix.
- **Honest Causal Tree** (Athey–Imbens). Recursively split subjects to *maximise
  how differently the treatment effect behaves* across groups, and estimate each
  group's effect on a held-out sample so the reported effects aren't biased by
  the same data that chose the splits.

## Testing

```bash
pytest -q          # 20 passing
```

The tests don't just check shapes — they assert the *science*: that correlation
sees the spurious `GeneA–GeneB` link, that partial correlation and the PC
algorithm remove it, and that the Causal Tree recovers the true responder
subgroup (effect ≈ 3.0) from the non-responders (effect ≈ 0.2).

---

*A koala can't tell which branch caused which just by looking at the leaves.
It has to climb. So do we.* 🐨🌳
