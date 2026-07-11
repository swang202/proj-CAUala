import numpy as np

from causala.ci_tests import fisher_z_test, is_independent, partial_corr


def _chain_data(n=3000, seed=0):
    # X0 -> X1 -> X2: X0 and X2 are dependent, but independent given X1.
    rng = np.random.default_rng(seed)
    x0 = rng.normal(0, 1, n)
    x1 = x0 + rng.normal(0, 0.5, n)
    x2 = x1 + rng.normal(0, 0.5, n)
    return np.column_stack([x0, x1, x2])


def test_marginal_dependence_detected():
    data = _chain_data()
    r, p = fisher_z_test(data, 0, 2, cond=())
    assert abs(r) > 0.5
    assert p < 0.01
    assert not is_independent(data, 0, 2, ())


def test_conditional_independence_detected():
    data = _chain_data()
    # X0 _||_ X2 | X1  (the defining feature of a causal chain)
    r, p = fisher_z_test(data, 0, 2, cond=(1,))
    assert abs(r) < 0.1
    assert is_independent(data, 0, 2, (1,))


def test_partial_corr_matches_pearson_when_unconditioned():
    data = _chain_data()
    r = partial_corr(data, 0, 1, ())
    pearson = np.corrcoef(data[:, 0], data[:, 1])[0, 1]
    assert abs(r - pearson) < 1e-9
