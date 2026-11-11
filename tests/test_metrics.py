import pytest

from evaluation.metrics import hit_at_k, reciprocal_rank


def test_hit_at_k_and_reciprocal_rank() -> None:
    retrieved = ["c3", "c1", "c2"]
    relevant = {"c1"}

    assert hit_at_k(retrieved, relevant, 1) == 0.0
    assert hit_at_k(retrieved, relevant, 2) == 1.0
    assert reciprocal_rank(retrieved, relevant) == 0.5


def test_metrics_reject_non_positive_k() -> None:
    with pytest.raises(ValueError, match="positive"):
        hit_at_k([], set(), 0)
