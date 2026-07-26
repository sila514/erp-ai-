"""Churn eşik optimizasyonu için saf fonksiyon testleri — DB gerektirmez."""
import numpy as np

from app.churn.train import _optimal_threshold


class TestOptimalThreshold:
    def test_perfectly_separable_scores_pick_a_threshold_between_classes(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_prob = np.array([0.1, 0.15, 0.2, 0.8, 0.85, 0.9])
        threshold, metrics = _optimal_threshold(y_true, y_prob)
        assert 0.2 < threshold <= 0.8
        assert metrics["f1"] == 1.0
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0

    def test_random_scores_still_return_a_valid_threshold(self):
        rng = np.random.default_rng(1)
        y_true = rng.integers(0, 2, size=100)
        y_prob = rng.random(100)
        threshold, metrics = _optimal_threshold(y_true, y_prob)
        assert 0.0 <= threshold <= 1.0
        assert 0.0 <= metrics["f1"] <= 1.0
