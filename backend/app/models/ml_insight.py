import uuid

from sqlalchemy import Column, String, DateTime, func, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class MLInsight(Base):
    """
    ML servisinden gelen sonuçların cache'lendiği genel tablo.
    insight_type: "demand_forecast" | "stock_risk" | "churn" | "segmentation" | "anomaly"
    entity_id: ilgili ürün/müşteri/işlem id'si
    payload: modelin döndürdüğü detaylı JSON (tahmin değeri, güven aralığı, SHAP değerleri vb.)
    """

    __tablename__ = "ml_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insight_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
