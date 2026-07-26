import uuid
from decimal import Decimal

from pydantic import BaseModel


class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str | None = None
    unit_price: Decimal
    unit_cost: Decimal
    stock_quantity: int = 0
    reorder_level: int = 10
    lead_time_days: int = 7


class ProductOut(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    category: str | None
    unit_price: Decimal
    unit_cost: Decimal
    stock_quantity: int
    reorder_level: int
    lead_time_days: int

    class Config:
        from_attributes = True


class StockRiskOut(BaseModel):
    """ML servisinden gelen stok tükenme riski sonucu (talep tahmininin
    belirsizliğinden — p10/p90 aralığından — hesaplanan güvenlik stoğu dahil)."""

    product_id: uuid.UUID
    current_stock: int
    predicted_daily_demand: float
    daily_demand_sigma: float
    days_until_stockout: float | None
    risk_level: str  # "low" | "medium" | "high"
    service_level: float
    safety_stock: float
    reorder_point: float
    recommended_reorder_quantity: int
    uncertainty_source: str  # "quantile_forecast" | "fallback_cv_30pct"
