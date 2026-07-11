"""From correlation to a causality matrix.

This module builds three views of the same data, each stricter than the last:

1. ``correlation_matrix`` — symmetric marginal association. Confounded pairs
   light up here even when there is no causal link.
2. ``partial_correlation_matrix`` — association after controlling for *all*
   other measured variables. Removes many, but not all, spurious links.
3. ``causal_discovery`` — the PC algorithm: learns a graph skeleton via
   conditional-independence tests, orients edges, and returns a directed
   **causality matrix** of estimated direct effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

from .ci_tests import fisher_z_test, is_independent


def correlation_matrix(data: pd.DataFrame) -> pd.DataFrame:
    """Plain Pearson correlation — the naive, correlation-only baseline."""
    return data.corr()


def partial_correlation_matrix(data: pd.DataFrame) -> pd.DataFrame:
    """Partial correlation controlling for every other column.

    Derived from the precision (inverse covariance) matrix::

        pcorr(i, j) = -P[i, j] / sqrt(P[i, i] * P[j, j])
    """
    cov = np.cov(data.values, rowvar=False)
    precision = np.linalg.pinv(cov)
    d = np.sqrt(np.diag(precision))
    pcorr = -precision / np.outer(d, d)
    np.fill_diagonal(pcorr, 1.0)
    return pd.DataFrame(pcorr, index=data.columns, columns=data.columns)


@dataclass
class CausalGraph:
    """Result of causal discovery.

    ``directed`` is the causality matrix: ``directed[i, j] != 0`` means a
    directed edge i -> j with the given estimated linear effect. ``undirected``
    holds edges whose orientation could not be determined from the data (they
    belong to the same Markov-equivalence class).
    """

    names: list[str]
    directed: np.ndarray
    undirected: np.ndarray  # symmetric 0/1 matrix of unoriented edges
    sepsets: dict[tuple[int, int], tuple[int, ...]]

    def causality_matrix(self) -> pd.DataFrame:
        return pd.DataFrame(self.directed, index=self.names, columns=self.names)

    def directed_edges(self) -> list[tuple[str, str, float]]:
        n = len(self.names)
        return [
            (self.names[i], self.names[j], float(self.directed[i, j]))
            for i in range(n)
            for j in range(n)
            if self.directed[i, j] != 0
        ]

    def undirected_edges(self) -> list[tuple[str, str]]:
        n = len(self.names)
        return [
            (self.names[i], self.names[j])
            for i in range(n)
            for j in range(i + 1, n)
            if self.undirected[i, j]
        ]


def _learn_skeleton(
    data: np.ndarray, alpha: float, max_cond: int
) -> tuple[np.ndarray, dict[tuple[int, int], tuple[int, ...]]]:
    """PC skeleton phase: prune the complete graph via CI tests."""
    p = data.shape[1]
    adj = np.ones((p, p), dtype=int) - np.eye(p, dtype=int)
    sepsets: dict[tuple[int, int], tuple[int, ...]] = {}

    order = 0
    while order <= max_cond:
        edges = list(zip(*np.where(np.triu(adj))))
        progressed = False
        for i, j in edges:
            if not adj[i, j]:
                continue
            neighbors = [k for k in range(p) if adj[i, k] and k != j]
            if len(neighbors) < order:
                continue
            progressed = True
            for cond in combinations(neighbors, order):
                if is_independent(data, i, j, cond, alpha=alpha):
                    adj[i, j] = adj[j, i] = 0
                    sepsets[(i, j)] = cond
                    sepsets[(j, i)] = cond
                    break
        if not progressed:
            break
        order += 1
    return adj, sepsets


def _orient_edges(
    adj: np.ndarray, sepsets: dict[tuple[int, int], tuple[int, ...]]
) -> np.ndarray:
    """Orient the skeleton into a CPDAG: v-structures, then Meek rules R1-R3.

    Returns a matrix ``g`` where ``g[i, j]==1 and g[j, i]==0`` is i -> j, and
    ``g[i, j]==g[j, i]==1`` is an undirected edge.
    """
    p = adj.shape[0]
    g = adj.copy()

    # v-structures: for unshielded triple i - k - j, if k not in sepset(i, j)
    # then orient i -> k <- j (a collider).
    for k in range(p):
        for i, j in combinations(range(p), 2):
            if adj[i, k] and adj[j, k] and not adj[i, j] and i != j:
                sep = sepsets.get((i, j))
                if sep is not None and k not in sep:
                    g[k, i] = 0  # i -> k
                    g[k, j] = 0  # j -> k

    # Meek rules, applied until no change.
    changed = True
    while changed:
        changed = False
        for i, j in combinations(range(p), 2):
            for a, b in ((i, j), (j, i)):
                if g[a, b] and g[b, a]:  # a - b undirected
                    # R1: c -> a - b and c not adjacent b  =>  a -> b
                    for c in range(p):
                        if c in (a, b):
                            continue
                        if g[c, a] and not g[a, c] and not (g[c, b] or g[b, c]):
                            g[b, a] = 0
                            changed = True
                            break
                    if not (g[a, b] and g[b, a]):
                        continue
                    # R2: a -> c -> b  =>  a -> b
                    for c in range(p):
                        if c in (a, b):
                            continue
                        if g[a, c] and not g[c, a] and g[c, b] and not g[b, c]:
                            g[b, a] = 0
                            changed = True
                            break
                    if not (g[a, b] and g[b, a]):
                        continue
                    # R3: a - c -> b, a - d -> b, c,d not adjacent  =>  a -> b
                    commons = [
                        c
                        for c in range(p)
                        if c not in (a, b)
                        and g[a, c] and g[c, a]
                        and g[c, b] and not g[b, c]
                    ]
                    for c, d in combinations(commons, 2):
                        if not (g[c, d] or g[d, c]):
                            g[b, a] = 0
                            changed = True
                            break
    return g


def _estimate_effects(data: np.ndarray, g: np.ndarray) -> np.ndarray:
    """Estimate the linear coefficient of each oriented edge i -> j.

    Regresses ``X_j`` on ``X_i`` together with j's other identified parents so
    the reported number is the *direct* effect, adjusted for confounding via
    the discovered parent set.
    """
    p = g.shape[0]
    effects = np.zeros((p, p))
    for j in range(p):
        parents = [i for i in range(p) if g[i, j] and not g[j, i]]
        if not parents:
            continue
        Z = np.column_stack([np.ones(data.shape[0])] + [data[:, i] for i in parents])
        beta, *_ = np.linalg.lstsq(Z, data[:, j], rcond=None)
        for k, i in enumerate(parents, start=1):
            effects[i, j] = beta[k]
    return effects


def causal_discovery(
    data: pd.DataFrame, alpha: float = 0.05, max_cond: int = 3
) -> CausalGraph:
    """Run the PC algorithm and return a directed causality matrix.

    Parameters
    ----------
    data:
        Observations, one column per variable.
    alpha:
        Significance level for the conditional-independence tests. Lower values
        yield sparser, higher-confidence graphs.
    max_cond:
        Largest conditioning set to test (caps runtime on dense graphs).
    """
    X = data.values.astype(float)
    names = list(data.columns)
    skeleton, sepsets = _learn_skeleton(X, alpha=alpha, max_cond=max_cond)
    g = _orient_edges(skeleton, sepsets)

    directed = _estimate_effects(X, g)
    p = len(names)
    undirected = np.zeros((p, p), dtype=int)
    for i in range(p):
        for j in range(p):
            if g[i, j] and g[j, i]:
                undirected[i, j] = 1

    return CausalGraph(
        names=names, directed=directed, undirected=undirected, sepsets=sepsets
    )
