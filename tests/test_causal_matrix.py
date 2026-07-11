import numpy as np

from causala.causal_matrix import (
    causal_discovery,
    correlation_matrix,
    partial_correlation_matrix,
)
from causala.datasets import gene_regulatory_network
from causala.metrics import edge_scores


def test_correlation_sees_spurious_link():
    ds = gene_regulatory_network(n_samples=2000, seed=10)
    corr = correlation_matrix(ds.data)
    # correlation is fooled: GeneA-GeneB looks strongly associated
    assert corr.loc["GeneA", "GeneB"] > 0.4


def test_partial_correlation_removes_confounded_link():
    ds = gene_regulatory_network(n_samples=3000, seed=11)
    pcorr = partial_correlation_matrix(ds.data)
    # controlling for TF (and the rest) collapses the GeneA-GeneB association
    assert abs(pcorr.loc["GeneA", "GeneB"]) < 0.1
    # but the true TF->GeneA link survives
    assert abs(pcorr.loc["TF", "GeneA"]) > 0.3


def test_causal_discovery_rejects_spurious_edge():
    ds = gene_regulatory_network(n_samples=3000, seed=12)
    graph = causal_discovery(ds.data, alpha=0.01)
    cm = graph.causality_matrix()
    # no direct edge (either direction) between the two confounded genes
    assert cm.loc["GeneA", "GeneB"] == 0
    assert cm.loc["GeneB", "GeneA"] == 0


def test_causal_discovery_recovers_true_structure():
    ds = gene_regulatory_network(n_samples=4000, seed=13)
    graph = causal_discovery(ds.data, alpha=0.01)
    pred = (graph.directed != 0).astype(int) + graph.undirected
    scores = edge_scores(ds.adjacency, pred)
    # skeleton should recover most true edges without inventing GeneA-GeneB
    assert scores["recall"] >= 0.8
    assert scores["false_positives"] <= 2


def test_causal_effect_signs_positive():
    ds = gene_regulatory_network(n_samples=4000, seed=14)
    graph = causal_discovery(ds.data, alpha=0.01)
    cm = graph.causality_matrix()
    # every true edge in this network has a positive weight; any recovered
    # oriented edge on the TF->Gene links should therefore be positive
    for a, b in [("TF", "GeneA"), ("TF", "GeneB")]:
        val = cm.loc[a, b] + cm.loc[b, a]
        if val != 0:
            assert val > 0
