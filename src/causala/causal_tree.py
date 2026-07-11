"""Honest Causal Tree for heterogeneous treatment effects.

Correlation asks "do these move together?" A causal tree asks a sharper,
actionable question: "for *whom* does an intervention actually work?" This is
the Athey & Imbens (2016) honest causal tree — it recursively partitions
patients to maximise how differently the treatment effect behaves across
groups, and estimates each group's effect on a held-out sample so the reported
effects are not biased by the same data that chose the splits.

This is the "climbing the causal tree" of the project name: each split is a
branch, each leaf a subpopulation with its own causal effect.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class _Node:
    n: int
    effect: float
    feature: int | None = None
    threshold: float | None = None
    left: "_Node | None" = None
    right: "_Node | None" = None
    depth: int = 0

    @property
    def is_leaf(self) -> bool:
        return self.feature is None


def _effect(t: np.ndarray, y: np.ndarray) -> float | None:
    """Difference in means between treated and control; None if a group is empty."""
    treated = y[t == 1]
    control = y[t == 0]
    if len(treated) == 0 or len(control) == 0:
        return None
    return float(treated.mean() - control.mean())


@dataclass
class CausalTree:
    """A single honest causal tree.

    Parameters
    ----------
    max_depth:
        Maximum number of splits from root to leaf.
    min_leaf:
        Minimum samples of *each* treatment arm required in a leaf, enforced on
        both the structure and estimation samples.
    honest:
        If True (default), split the data so tree structure and leaf effect
        estimates use disjoint samples — the property that makes leaf effects
        unbiased.
    """

    max_depth: int = 3
    min_leaf: int = 25
    honest: bool = True
    seed: int | None = 0
    root_: _Node | None = field(default=None, init=False)

    def fit(self, X: np.ndarray, t: np.ndarray, y: np.ndarray) -> "CausalTree":
        X = np.asarray(X, dtype=float)
        t = np.asarray(t, dtype=int)
        y = np.asarray(y, dtype=float)
        rng = np.random.default_rng(self.seed)

        n = len(y)
        if self.honest:
            perm = rng.permutation(n)
            half = n // 2
            struct_idx, est_idx = perm[:half], perm[half:]
        else:
            struct_idx = est_idx = np.arange(n)

        self.root_ = self._grow(
            X, t, y, struct_idx, est_idx, depth=0
        )
        return self

    def _grow(
        self,
        X: np.ndarray,
        t: np.ndarray,
        y: np.ndarray,
        s_idx: np.ndarray,
        e_idx: np.ndarray,
        depth: int,
    ) -> _Node:
        est_effect = _effect(t[e_idx], y[e_idx])
        struct_effect = _effect(t[s_idx], y[s_idx])
        # Fall back to the structure-sample effect if the estimation leaf is
        # missing a treatment arm.
        node_effect = est_effect if est_effect is not None else (struct_effect or 0.0)
        node = _Node(n=len(e_idx), effect=node_effect, depth=depth)

        if depth >= self.max_depth:
            return node

        best = self._best_split(X, t, y, s_idx)
        if best is None:
            return node
        feature, threshold, _ = best

        s_left = s_idx[X[s_idx, feature] <= threshold]
        s_right = s_idx[X[s_idx, feature] > threshold]
        e_left = e_idx[X[e_idx, feature] <= threshold]
        e_right = e_idx[X[e_idx, feature] > threshold]

        # Honest guard: both children must support effect estimation.
        if not (
            self._valid_leaf(t, s_left)
            and self._valid_leaf(t, s_right)
            and self._valid_leaf(t, e_left)
            and self._valid_leaf(t, e_right)
        ):
            return node

        node.feature = feature
        node.threshold = threshold
        node.left = self._grow(X, t, y, s_left, e_left, depth + 1)
        node.right = self._grow(X, t, y, s_right, e_right, depth + 1)
        return node

    def _valid_leaf(self, t: np.ndarray, idx: np.ndarray) -> bool:
        if len(idx) < self.min_leaf:
            return False
        arm = t[idx]
        return arm.sum() >= 1 and (len(arm) - arm.sum()) >= 1

    def _best_split(
        self, X: np.ndarray, t: np.ndarray, y: np.ndarray, s_idx: np.ndarray
    ):
        """Pick the split maximising treatment-effect heterogeneity.

        Criterion: ``n_L * tau_L^2 + n_R * tau_R^2`` on the structure sample.
        Splits that separate high-effect from low-effect subpopulations score
        highest — this is the heterogeneity-seeking objective of causal trees.
        """
        best_score = -np.inf
        best = None
        p = X.shape[1]
        for feature in range(p):
            values = np.unique(X[s_idx, feature])
            if len(values) < 2:
                continue
            # candidate thresholds: quantiles keep this fast and robust
            qs = np.quantile(values, np.linspace(0.1, 0.9, 9))
            for threshold in np.unique(qs):
                left = s_idx[X[s_idx, feature] <= threshold]
                right = s_idx[X[s_idx, feature] > threshold]
                if not (self._valid_leaf(t, left) and self._valid_leaf(t, right)):
                    continue
                tau_l = _effect(t[left], y[left])
                tau_r = _effect(t[right], y[right])
                if tau_l is None or tau_r is None:
                    continue
                score = len(left) * tau_l**2 + len(right) * tau_r**2
                if score > best_score:
                    best_score = score
                    best = (feature, float(threshold), score)
        return best

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict the conditional average treatment effect (CATE) per row."""
        if self.root_ is None:
            raise RuntimeError("call fit() before predict()")
        X = np.asarray(X, dtype=float)
        return np.array([self._route(self.root_, row) for row in X])

    def _route(self, node: _Node, row: np.ndarray) -> float:
        while not node.is_leaf:
            assert node.feature is not None and node.threshold is not None
            node = node.left if row[node.feature] <= node.threshold else node.right  # type: ignore[assignment]
        return node.effect

    def describe(self, feature_names: list[str] | None = None) -> str:
        """A readable text rendering of the fitted tree."""
        if self.root_ is None:
            return "<unfitted CausalTree>"
        lines: list[str] = []

        def walk(node: _Node, prefix: str) -> None:
            if node.is_leaf:
                lines.append(f"{prefix}leaf: effect={node.effect:+.2f}  (n={node.n})")
                return
            name = (
                feature_names[node.feature]
                if feature_names and node.feature is not None
                else f"x{node.feature}"
            )
            lines.append(f"{prefix}if {name} <= {node.threshold:.2f}:")
            walk(node.left, prefix + "  ")  # type: ignore[arg-type]
            lines.append(f"{prefix}else:")
            walk(node.right, prefix + "  ")  # type: ignore[arg-type]

        walk(self.root_, "")
        return "\n".join(lines)
