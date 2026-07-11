"""Scoring recovered graphs against ground truth.

Because the synthetic datasets ship with their true causal graph, we can put a
number on how well a method separates causation from correlation.
"""

from __future__ import annotations

import numpy as np


def _binarize(mat: np.ndarray) -> np.ndarray:
    return (np.asarray(mat) != 0).astype(int)


def edge_scores(true_adj: np.ndarray, pred_adj: np.ndarray) -> dict[str, float]:
    """Precision / recall / F1 over *directed* edges.

    An edge counts as correct only if it exists in the truth with the same
    orientation.
    """
    T = _binarize(true_adj)
    P = _binarize(pred_adj)
    np.fill_diagonal(T, 0)
    np.fill_diagonal(P, 0)

    tp = int(np.sum((T == 1) & (P == 1)))
    fp = int(np.sum((T == 0) & (P == 1)))
    fn = int(np.sum((T == 1) & (P == 0)))

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def structural_hamming_distance(true_adj: np.ndarray, pred_adj: np.ndarray) -> int:
    """Number of edge insertions/deletions/reversals to turn pred into truth.

    Treats each unordered pair once: a missing edge, an extra edge, or a
    reversed edge each cost 1.
    """
    T = _binarize(true_adj)
    P = _binarize(pred_adj)
    p = T.shape[0]
    shd = 0
    for i in range(p):
        for j in range(i + 1, p):
            t_ij, t_ji = T[i, j], T[j, i]
            p_ij, p_ji = P[i, j], P[j, i]
            if (t_ij, t_ji) != (p_ij, p_ji):
                shd += 1
    return shd
