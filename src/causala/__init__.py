"""causala — climbing the causal tree 🐨.

A small, dependency-light toolkit for telling causation from correlation in
biological data. Three layers, from loosest to strictest:

* correlation & partial-correlation matrices (the naive baselines),
* the PC algorithm producing a directed **causality matrix**, and
* an honest **Causal Tree** for heterogeneous treatment effects.

Everything runs on numpy / scipy / pandas.
"""

from __future__ import annotations

from .causal_matrix import (
    CausalGraph,
    causal_discovery,
    correlation_matrix,
    partial_correlation_matrix,
)
from .causal_tree import CausalTree
from .ci_tests import fisher_z_test, is_independent, partial_corr
from .datasets import (
    CausalDataset,
    gene_regulatory_network,
    simulate_sem,
    treatment_response,
)
from .metrics import edge_scores, structural_hamming_distance

__version__ = "0.1.0"

__all__ = [
    "CausalGraph",
    "CausalDataset",
    "CausalTree",
    "causal_discovery",
    "correlation_matrix",
    "partial_correlation_matrix",
    "fisher_z_test",
    "is_independent",
    "partial_corr",
    "gene_regulatory_network",
    "simulate_sem",
    "treatment_response",
    "edge_scores",
    "structural_hamming_distance",
    "__version__",
]
