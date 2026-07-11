import numpy as np
import pytest

from causala.datasets import (
    gene_regulatory_network,
    simulate_sem,
    treatment_response,
)


def test_sem_respects_topology():
    # X0 -> X1 -> X2 chain
    A = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]])
    W = np.array([[0, 2.0, 0], [0, 0, 2.0], [0, 0, 0]])
    X = simulate_sem(A, W, n_samples=2000, noise_scale=0.1, seed=1)
    # downstream variance grows because signal accumulates through the chain
    assert X[:, 2].var() > X[:, 0].var()


def test_sem_rejects_cycles():
    A = np.array([[0, 1], [1, 0]])
    W = np.array([[0, 1.0], [1.0, 0]])
    with pytest.raises(ValueError):
        simulate_sem(A, W, n_samples=10, seed=0)


def test_grn_shape_and_edges():
    ds = gene_regulatory_network(n_samples=300, seed=3)
    assert ds.data.shape == (300, 7)
    assert ("TF", "GeneA") in ds.edges()
    assert ("TF", "GeneB") in ds.edges()
    # no direct GeneA<->GeneB edge exists in the ground truth
    assert ("GeneA", "GeneB") not in ds.edges()
    assert ("GeneB", "GeneA") not in ds.edges()


def test_grn_confounding_creates_correlation():
    ds = gene_regulatory_network(n_samples=2000, seed=4)
    # despite no causal link, GeneA and GeneB are strongly correlated via TF
    r = ds.data["GeneA"].corr(ds.data["GeneB"])
    assert r > 0.4


def test_treatment_response_columns():
    df, t, y, cov = treatment_response(n_samples=500, seed=5)
    assert t == "treatment"
    assert y == "outcome"
    assert set(cov) == {"biomarker", "age", "noise_gene1", "noise_gene2"}
    assert set(df[t].unique()) <= {0, 1}
