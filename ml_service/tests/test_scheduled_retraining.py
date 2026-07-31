"""Zamanlanmış yeniden eğitim orkestrasyonu için testler — gerçek DB veya
model eğitimi yok; train_* fonksiyonları ve DB session'ı mock'lanır."""
from unittest.mock import MagicMock, patch

from app.scheduler.retrain import (
    list_trainable_product_ids,
    retrain_anomaly_model,
    retrain_churn_model,
    retrain_demand_forecast_models,
    run_scheduled_retraining,
)


class TestListTrainableProductIds:
    def test_enumerates_products_returned_by_query(self):
        db = MagicMock()
        db.execute.return_value.fetchall.return_value = [("p1",), ("p2",)]
        result = list_trainable_product_ids(db)
        assert result == ["p1", "p2"]


class TestRetrainDemandForecastModels:
    @patch("app.scheduler.retrain.train_demand_model")
    @patch("app.scheduler.retrain.list_trainable_product_ids", return_value=["p1", "p2"])
    @patch("app.scheduler.retrain.SessionLocal")
    def test_calls_train_for_each_enumerated_product(self, mock_session, mock_list_ids, mock_train):
        result = retrain_demand_forecast_models()

        assert mock_train.call_count == 2
        mock_train.assert_any_call("p1", report=True)
        mock_train.assert_any_call("p2", report=True)
        assert result["trained"] == ["p1", "p2"]
        assert result["failed"] == {}

    @patch("app.scheduler.retrain.train_demand_model")
    @patch("app.scheduler.retrain.list_trainable_product_ids", return_value=["p1", "p2"])
    @patch("app.scheduler.retrain.SessionLocal")
    def test_isolates_failure_of_one_product_and_continues(self, mock_session, mock_list_ids, mock_train):
        mock_train.side_effect = [ValueError("yetersiz veri"), None]

        result = retrain_demand_forecast_models()

        assert result["trained"] == ["p2"]
        assert "p1" in result["failed"]
        assert mock_train.call_count == 2


class TestRetrainChurnModel:
    @patch("app.scheduler.retrain.train_churn_model")
    def test_success(self, mock_train):
        result = retrain_churn_model()
        mock_train.assert_called_once_with(report=True)
        assert result == {"model": "churn", "trained": True, "failed": None}

    @patch("app.scheduler.retrain.train_churn_model", side_effect=ValueError("boom"))
    def test_failure_does_not_raise(self, mock_train):
        result = retrain_churn_model()
        assert result["trained"] is False
        assert "boom" in result["failed"]


class TestRetrainAnomalyModel:
    @patch("app.scheduler.retrain.train_anomaly_model")
    def test_success(self, mock_train):
        result = retrain_anomaly_model()
        mock_train.assert_called_once_with(report=True)
        assert result == {"model": "anomaly_detection", "trained": True, "failed": None}

    @patch("app.scheduler.retrain.train_anomaly_model", side_effect=ValueError("boom"))
    def test_failure_does_not_raise(self, mock_train):
        result = retrain_anomaly_model()
        assert result["trained"] is False
        assert "boom" in result["failed"]


class TestRunScheduledRetraining:
    @patch("app.scheduler.retrain.retrain_anomaly_model")
    @patch("app.scheduler.retrain.retrain_churn_model")
    @patch("app.scheduler.retrain.retrain_demand_forecast_models")
    def test_runs_all_three_models_and_continues_past_failures(
        self, mock_demand, mock_churn, mock_anomaly
    ):
        mock_demand.return_value = {"model": "demand_forecast", "trained": [], "failed": {"p1": "err"}}
        mock_churn.return_value = {"model": "churn", "trained": False, "failed": "err"}
        mock_anomaly.return_value = {"model": "anomaly_detection", "trained": True, "failed": None}

        result = run_scheduled_retraining()

        assert mock_demand.called and mock_churn.called and mock_anomaly.called
        assert result["anomaly_detection"]["trained"] is True
