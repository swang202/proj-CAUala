"""Conditional-independence tests.

The heart of "beyond correlation": two variables can be strongly correlated
yet *conditionally independent* once we control for a common cause. These tests
are the primitives the causal-discovery algorithms are built on.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def partial_corr(data: np.ndarray, i: int, j: int, cond: tuple[int, ...]) -> float:
    """Partial correlation of columns ``i`` and ``j`` given columns ``cond``.

    Computed by regressing out the conditioning set from both variables and
    correlating the residuals. With an empty conditioning set this reduces to
    the ordinary Pearson correlation.
    """
    x = data[:, i]
    y = data[:, j]
    if cond:
        z = data[:, list(cond)]
        z = np.column_stack([np.ones(len(z)), z])
        # residuals after least-squares projection onto the conditioning set
        beta_x, *_ = np.linalg.lstsq(z, x, rcond=None)
        beta_y, *_ = np.linalg.lstsq(z, y, rcond=None)
        x = x - z @ beta_x
        y = y - z @ beta_y
    sx = x.std()
    sy = y.std()
    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    r = float(np.mean((x - x.mean()) * (y - y.mean())) / (sx * sy))
    return max(-0.9999999, min(0.9999999, r))


def fisher_z_test(
    data: np.ndarray, i: int, j: int, cond: tuple[int, ...]
) -> tuple[float, float]:
    """Fisher's Z test for (conditional) independence of columns ``i`` and ``j``.

    Returns ``(partial_correlation, p_value)``. Under the null of zero partial
    correlation, the Fisher-transformed statistic is asymptotically normal.
    """
    n = data.shape[0]
    dof = len(cond)
    r = partial_corr(data, i, j, cond)
    if n - dof - 3 <= 0:
        # not enough degrees of freedom to test; treat as dependent
        return r, 0.0
    z = 0.5 * np.log((1 + r) / (1 - r))
    stat = np.sqrt(n - dof - 3) * abs(z)
    p = 2 * (1 - stats.norm.cdf(stat))
    return r, float(p)


def is_independent(
    data: np.ndarray, i: int, j: int, cond: tuple[int, ...], alpha: float = 0.05
) -> bool:
    """Return ``True`` if ``i`` and ``j`` are independent given ``cond`` at level ``alpha``."""
    _, p = fisher_z_test(data, i, j, cond)
    return p > alpha
