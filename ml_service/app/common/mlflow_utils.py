"""
MLflow deney takibi — yerel dosya tabanlı (`./mlruns`, ayrı bir MLflow server
container'ı yok). Sunum/inference hâlâ joblib dosyalarından yapılır; MLflow
sadece deney takibi + parametre/metrik/artifact kaydı için ikincil bir kayıttır.
"""
import mlflow

MLFLOW_TRACKING_URI = "file:./mlruns"


def configure_mlflow(experiment_name: str) -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(experiment_name)
