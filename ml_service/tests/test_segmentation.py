"""Segmentasyon için saf fonksiyon testleri — DB gerektirmez, sentetik veriyle."""
import numpy as np
import pandas as pd

from app.customer_segmentation.service import K_RANGE, label_clusters, select_optimal_k


class TestSelectOptimalK:
    def test_recovers_a_reasonable_k_for_well_separated_clusters(self):
        rng = np.random.default_rng(42)
        cluster_a = rng.normal(loc=[-5, -5, -5], scale=0.3, size=(30, 3))
        cluster_b = rng.normal(loc=[0, 0, 0], scale=0.3, size=(30, 3))
        cluster_c = rng.normal(loc=[5, 5, 5], scale=0.3, size=(30, 3))
        data = np.vstack([cluster_a, cluster_b, cluster_c])

        best_k, silhouette_scores, inertias = select_optimal_k(data)

        assert best_k in K_RANGE
        # Üç bariz ayrık küme varken silhouette skoru çok yüksek olmalı (>0.7)
        assert silhouette_scores[best_k] > 0.7
        assert set(silhouette_scores.keys()) == set(inertias.keys())

    def test_inertia_decreases_as_k_increases(self):
        rng = np.random.default_rng(1)
        data = rng.normal(size=(100, 3))
        _, _, inertias = select_optimal_k(data)
        ks = sorted(inertias.keys())
        assert all(inertias[ks[i]] >= inertias[ks[i + 1]] for i in range(len(ks) - 1))


class TestLabelClusters:
    def _build_df(self) -> pd.DataFrame:
        rows = []
        # sadık_müşteri: düşük recency + yüksek frequency/monetary
        for _ in range(5):
            rows.append({"cluster": 0, "recency_z": -1.0, "frequency_z": 1.0, "monetary_z": 1.0, "tenure_days": 200})
        # yüksek_değerli: yüksek monetary + düşük tenure
        for _ in range(5):
            rows.append({"cluster": 1, "recency_z": 0.0, "frequency_z": 0.0, "monetary_z": 1.2, "tenure_days": 10})
        # yeni_müşteri: düşük frequency + düşük tenure
        for _ in range(5):
            rows.append({"cluster": 2, "recency_z": 0.0, "frequency_z": -1.0, "monetary_z": 0.0, "tenure_days": 15})
        # risk_altında: yüksek recency
        for _ in range(5):
            rows.append({"cluster": 3, "recency_z": 1.0, "frequency_z": 0.0, "monetary_z": 0.0, "tenure_days": 200})
        # eşleşmeyen: tüm z-skorlar nötr
        for _ in range(5):
            rows.append({"cluster": 4, "recency_z": 0.0, "frequency_z": 0.0, "monetary_z": 0.0, "tenure_days": 150})
        return pd.DataFrame(rows)

    def test_assigns_expected_archetypal_labels(self):
        df = self._build_df()
        labels = label_clusters(df)
        assert labels[0] == "sadık_müşteri"
        assert labels[1] == "yüksek_değerli"
        assert labels[2] == "yeni_müşteri"
        assert labels[3] == "risk_altında"

    def test_unmatched_cluster_falls_back_to_generic_segment_name(self):
        df = self._build_df()
        labels = label_clusters(df)
        assert labels[4] == "segment_4"
