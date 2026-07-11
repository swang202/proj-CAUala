import numpy as np

from causala.metrics import edge_scores, structural_hamming_distance


def test_perfect_recovery():
    true = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]])
    scores = edge_scores(true, true)
    assert scores["precision"] == 1.0
    assert scores["recall"] == 1.0
    assert scores["f1"] == 1.0
    assert structural_hamming_distance(true, true) == 0


def test_reversed_edge_counts_once():
    true = np.array([[0, 1], [0, 0]])
    pred = np.array([[0, 0], [1, 0]])  # reversed
    assert structural_hamming_distance(true, pred) == 1
    scores = edge_scores(true, pred)
    assert scores["recall"] == 0.0


def test_missing_and_extra_edges():
    true = np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]])
    pred = np.array([[0, 0, 1], [0, 0, 0], [0, 0, 0]])  # wrong edge
    scores = edge_scores(true, pred)
    assert scores["false_positives"] == 1
    assert scores["false_negatives"] == 1
    assert structural_hamming_distance(true, pred) == 2
