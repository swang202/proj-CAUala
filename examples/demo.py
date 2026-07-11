"""End-to-end demo: climbing the causal tree.

Run with::

    python examples/demo.py

It walks through the project's core claim — that correlation is not causation —
on simulated biological data, and saves figures to ``examples/figures/``.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from causala import (
    CausalTree,
    causal_discovery,
    correlation_matrix,
    edge_scores,
    gene_regulatory_network,
    partial_correlation_matrix,
    structural_hamming_distance,
    treatment_response,
)

FIG_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIG_DIR, exist_ok=True)

KOALA_GREEN = "#3f7d5a"
KOALA_GREY = "#6b7280"


def banner(text: str) -> None:
    print("\n" + "=" * 68)
    print(f"  {text}")
    print("=" * 68)


def part_one_causality_matrix() -> None:
    banner("Part 1 — from a correlation matrix to a causality matrix")
    ds = gene_regulatory_network(n_samples=3000, seed=42)
    print(ds.description)
    print("True causal edges:")
    for a, b in ds.edges():
        print(f"    {a:>9} -> {b}")

    corr = correlation_matrix(ds.data)
    pcorr = partial_correlation_matrix(ds.data)
    graph = causal_discovery(ds.data, alpha=0.01)
    cm = graph.causality_matrix()

    print(
        f"\nGeneA-GeneB association (they share TF as a common cause, "
        f"NO direct link):"
    )
    print(f"    correlation           : {corr.loc['GeneA', 'GeneB']:+.3f}  <- misleading!")
    print(f"    partial correlation   : {pcorr.loc['GeneA', 'GeneB']:+.3f}  <- confound removed")
    print(f"    causality matrix edge : {cm.loc['GeneA', 'GeneB']:+.3f}  <- correctly absent")

    pred = (graph.directed != 0).astype(int) + graph.undirected
    scores = edge_scores(ds.adjacency, pred)
    shd = structural_hamming_distance(ds.adjacency, pred)
    print("\nStructure recovery vs ground truth:")
    print(f"    precision={scores['precision']:.2f}  recall={scores['recall']:.2f}  "
          f"F1={scores['f1']:.2f}  SHD={shd}")

    print("\nDiscovered directed causal effects:")
    for a, b, w in graph.directed_edges():
        print(f"    {a:>9} -> {b:<9}  effect={w:+.2f}")

    _plot_matrices(corr, cm, ds.names)


def _plot_matrices(corr, cm, names) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    axes[0].set_title("Correlation matrix\n(symmetric, dense, confounded)")
    axes[1].imshow(cm.values, cmap="RdBu_r", vmin=-1.5, vmax=1.5)
    axes[1].set_title("Causality matrix\n(directed, sparse, causal)")
    for ax in axes:
        ax.set_xticks(range(len(names)))
        ax.set_yticks(range(len(names)))
        ax.set_xticklabels(names, rotation=45, ha="right")
        ax.set_yticklabels(names)
    fig.suptitle("Same data, two very different stories", fontweight="bold")
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "correlation_vs_causality.png")
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"\n  saved figure -> {out}")


def part_two_causal_tree() -> None:
    banner("Part 2 — climbing the causal tree: who does the drug help?")
    df, t, y, cov = treatment_response(n_samples=5000, seed=42)

    naive = df[df[t] == 1][y].mean() - df[df[t] == 0][y].mean()
    print(f"Naive average treatment effect (whole cohort): {naive:+.2f}")
    print("...but this single number hides who actually benefits.\n")

    tree = CausalTree(max_depth=3, min_leaf=60, seed=1).fit(
        df[cov].values, df[t].values, df[y].values
    )
    print("Fitted honest causal tree:")
    print(tree.describe(feature_names=cov))

    cate = tree.predict(df[cov].values)
    responders = df["biomarker"] > 0.3
    print(f"\nPredicted effect for high-biomarker patients : {cate[responders].mean():+.2f}")
    print(f"Predicted effect for low-biomarker patients  : {cate[~responders].mean():+.2f}")
    print(f"True effects were 3.0 and 0.2 respectively.")

    corr_est = np.corrcoef(cate, df["true_cate"].values)[0, 1]
    print(f"Correlation of predicted vs true CATE: {corr_est:.3f}")

    _plot_cate(df, cate)


def _plot_cate(df, cate) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df["biomarker"], cate, s=8, alpha=0.4, color=KOALA_GREEN,
               label="estimated CATE")
    ax.scatter(df["biomarker"], df["true_cate"], s=8, alpha=0.3, color=KOALA_GREY,
               label="true CATE")
    ax.axvline(0.3, ls="--", color="black", lw=1, label="true threshold")
    ax.set_xlabel("biomarker")
    ax.set_ylabel("treatment effect")
    ax.set_title("Causal tree recovers the responder subgroup")
    ax.legend()
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "cate_by_biomarker.png")
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"\n  saved figure -> {out}")


if __name__ == "__main__":
    part_one_causality_matrix()
    part_two_causal_tree()
    banner("Done. The koala reached the top of the causal tree.")
