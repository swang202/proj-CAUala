"""Synthetic biological datasets with *known* causal ground truth.

The whole point of the project is to tell causation from correlation. To
measure whether we succeed, we need data where the true causal graph is known.
These simulators draw from linear structural equation models (SEMs) — the
standard workhorse for benchmarking causal-discovery methods — dressed up as
small biological systems.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class CausalDataset:
    """A dataset bundled with its ground-truth directed causal graph."""

    data: pd.DataFrame
    adjacency: np.ndarray  # adjacency[i, j] == 1 means i -> j (i causes j)
    names: list[str]
    description: str = ""

    @property
    def n_nodes(self) -> int:
        return len(self.names)

    def edges(self) -> list[tuple[str, str]]:
        """Ground-truth directed edges as (cause, effect) name pairs."""
        return [
            (self.names[i], self.names[j])
            for i in range(self.n_nodes)
            for j in range(self.n_nodes)
            if self.adjacency[i, j]
        ]


def simulate_sem(
    adjacency: np.ndarray,
    weights: np.ndarray,
    n_samples: int,
    noise_scale: float = 1.0,
    seed: int | None = None,
) -> np.ndarray:
    """Sample from a linear-Gaussian SEM defined by a DAG.

    Each variable is generated in topological order as a weighted sum of its
    parents plus independent Gaussian noise::

        X_j = sum_i weights[i, j] * X_i + noise_j

    ``adjacency`` must be a DAG (acyclic); ``weights`` carries the edge
    coefficients (only entries where ``adjacency`` is 1 are used).
    """
    rng = np.random.default_rng(seed)
    p = adjacency.shape[0]
    order = _topological_order(adjacency)
    X = np.zeros((n_samples, p))
    for j in order:
        parents = np.where(adjacency[:, j])[0]
        signal = X[:, parents] @ weights[parents, j] if len(parents) else 0.0
        X[:, j] = signal + rng.normal(0.0, noise_scale, size=n_samples)
    return X


def _topological_order(adjacency: np.ndarray) -> list[int]:
    """Kahn's algorithm; raises if the graph has a cycle."""
    p = adjacency.shape[0]
    indeg = adjacency.sum(axis=0).astype(int).tolist()
    order: list[int] = []
    frontier = [i for i in range(p) if indeg[i] == 0]
    while frontier:
        node = frontier.pop()
        order.append(node)
        for child in np.where(adjacency[node])[0]:
            indeg[child] -= 1
            if indeg[child] == 0:
                frontier.append(int(child))
    if len(order) != p:
        raise ValueError("adjacency matrix is not a DAG (contains a cycle)")
    return order


def gene_regulatory_network(
    n_samples: int = 500, noise_scale: float = 0.6, seed: int | None = 7
) -> CausalDataset:
    """A small signalling cascade with a confounder.

    The topology encodes a classic trap for correlation-only analysis::

        Ligand -> Receptor -> Kinase -> TF -> {GeneA, GeneB}
        Stress -> Kinase                    (a second input to the kinase)

    ``GeneA`` and ``GeneB`` share the transcription factor ``TF`` as a common
    cause, so they are strongly *correlated* yet have **no** direct causal link.
    Any honest causality method must refuse to draw a GeneA<->GeneB edge.
    """
    names = ["Ligand", "Stress", "Receptor", "Kinase", "TF", "GeneA", "GeneB"]
    idx = {n: k for k, n in enumerate(names)}
    p = len(names)
    A = np.zeros((p, p), dtype=int)
    W = np.zeros((p, p))

    def edge(src: str, dst: str, w: float) -> None:
        A[idx[src], idx[dst]] = 1
        W[idx[src], idx[dst]] = w

    edge("Ligand", "Receptor", 1.1)
    edge("Receptor", "Kinase", 0.9)
    edge("Stress", "Kinase", 0.8)
    edge("Kinase", "TF", 1.2)
    edge("TF", "GeneA", 1.0)
    edge("TF", "GeneB", 0.95)

    X = simulate_sem(A, W, n_samples, noise_scale=noise_scale, seed=seed)
    df = pd.DataFrame(X, columns=names)
    return CausalDataset(
        data=df,
        adjacency=A,
        names=names,
        description="Signalling cascade; GeneA & GeneB are correlated confounds via TF.",
    )


def treatment_response(
    n_samples: int = 2000, seed: int | None = 11
) -> tuple[pd.DataFrame, str, str, list[str]]:
    """A drug-response cohort with a *heterogeneous* treatment effect.

    A drug is given at random (a simulated randomized trial). Its true causal
    effect on the outcome depends on a biomarker: patients whose ``biomarker``
    is high benefit substantially, while low-biomarker patients do not. Age and
    a couple of noise genes are thrown in as distractor covariates.

    Returns ``(dataframe, treatment_col, outcome_col, covariate_cols)``. The
    per-patient ground-truth effect is stored in the ``true_cate`` column.
    """
    rng = np.random.default_rng(seed)
    biomarker = rng.normal(0, 1, n_samples)
    age = rng.uniform(20, 80, n_samples)
    noise_gene1 = rng.normal(0, 1, n_samples)
    noise_gene2 = rng.normal(0, 1, n_samples)

    treatment = rng.integers(0, 2, n_samples)  # randomized assignment

    # True conditional effect: only high-biomarker patients respond.
    true_cate = np.where(biomarker > 0.3, 3.0, 0.2)

    baseline = 0.5 * age / 10 + 0.8 * biomarker + rng.normal(0, 1.0, n_samples)
    outcome = baseline + treatment * true_cate

    df = pd.DataFrame(
        {
            "biomarker": biomarker,
            "age": age,
            "noise_gene1": noise_gene1,
            "noise_gene2": noise_gene2,
            "treatment": treatment,
            "outcome": outcome,
            "true_cate": true_cate,
        }
    )
    covariates = ["biomarker", "age", "noise_gene1", "noise_gene2"]
    return df, "treatment", "outcome", covariates
