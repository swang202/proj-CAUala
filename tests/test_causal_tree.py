import numpy as np

from causala.causal_tree import CausalTree
from causala.datasets import treatment_response


def test_tree_recovers_heterogeneous_effect():
    df, t, y, cov = treatment_response(n_samples=4000, seed=20)
    tree = CausalTree(max_depth=3, min_leaf=50, seed=1).fit(
        df[cov].values, df[t].values, df[y].values
    )
    cate = tree.predict(df[cov].values)

    high = df["biomarker"] > 0.3
    # responders (high biomarker) get a much larger predicted effect
    assert cate[high].mean() > cate[~high].mean() + 1.0
    # and the estimate lands near the true effect of ~3.0 for responders
    assert 2.0 < cate[high].mean() < 4.0


def test_tree_splits_on_true_biomarker():
    df, t, y, cov = treatment_response(n_samples=4000, seed=21)
    tree = CausalTree(max_depth=2, min_leaf=50, seed=2).fit(
        df[cov].values, df[t].values, df[y].values
    )
    text = tree.describe(feature_names=cov)
    # the biomarker is the real modifier, so it should appear as a split
    assert "biomarker" in text


def test_predict_before_fit_raises():
    tree = CausalTree()
    try:
        tree.predict(np.zeros((3, 2)))
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_honest_and_adaptive_agree_directionally():
    df, t, y, cov = treatment_response(n_samples=4000, seed=22)
    X, T, Y = df[cov].values, df[t].values, df[y].values
    honest = CausalTree(honest=True, seed=3).fit(X, T, Y).predict(X)
    adaptive = CausalTree(honest=False, seed=3).fit(X, T, Y).predict(X)
    high = df["biomarker"] > 0.3
    assert honest[high].mean() > honest[~high].mean()
    assert adaptive[high].mean() > adaptive[~high].mean()
