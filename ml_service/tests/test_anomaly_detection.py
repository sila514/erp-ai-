"""Anomali tespiti eğitim yardımcıları için saf fonksiyon testleri — DB gerektirmez."""
import numpy as np

from app.anomaly_detection.train import _inject_synthetic_anomalies, _precision_at_k


class TestInjectSyntheticAnomalies:
    def test_output_size_and_label_counts(self):
        rng = np.random.default_rng(0)
        normal = rng.normal(loc=[100, 2, 12, 0], scale=[20, 1, 4, 0.5], size=(50, 4))
        combined, labels = _inject_synthetic_anomalies(normal, n=10, rng=rng)
        assert combined.shape == (60, 4)
        assert labels.sum() == 10
        assert (labels[:50] == 0).all()

    def test_injected_points_have_inflated_amount_and_item_count(self):
        rng = np.random.default_rng(0)
        normal = np.tile(np.array([[100.0, 2.0, 12.0, 0.0]]), (20, 1))
        combined, labels = _inject_synthetic_anomalies(normal, n=5, rng=rng)
        injected = combined[labels == 1]
        assert (injected[:, 0] > 100).all()  # total_amount büyütülmüş
        assert (injected[:, 1] > 2).all()  # item_count büyütülmüş


class TestPrecisionAtK:
    def test_perfect_ranking_gives_precision_one(self):
        # düşük skor = daha anormal; ilk k eleman gerçek anomali olsun
        scores = np.array([-5, -4, -3, 1, 2, 3])
        labels = np.array([1, 1, 1, 0, 0, 0])
        assert _precision_at_k(scores, labels, k=3) == 1.0

    def test_random_ranking_gives_lower_precision(self):
        scores = np.array([1, -5, 2, -4, 3, -3])  # anomaliler sona serpiştirildi
        labels = np.array([0, 1, 0, 1, 0, 1])
        # en düşük 3 skor: -5,-4,-3 -> hepsi labels=1 olan indexlerde, yine 1.0 olmalı
        assert _precision_at_k(scores, labels, k=3) == 1.0

    def test_no_overlap_gives_zero_precision(self):
        scores = np.array([-5, -4, -3, 1, 2, 3])
        labels = np.array([0, 0, 0, 1, 1, 1])  # en anormal 3 nokta hiçbiri gerçek anomali değil
        assert _precision_at_k(scores, labels, k=3) == 0.0
