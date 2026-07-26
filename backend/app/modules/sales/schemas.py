import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.sale import SaleStatus


class SaleItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal


class SaleCreate(BaseModel):
    customer_id: uuid.UUID
    items: list[SaleItemCreate]


class SaleItemOut(BaseModel):
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal

    class Config:
        from_attributes = True


class SaleOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    status: SaleStatus
    total_amount: Decimal
    is_flagged_anomaly: bool
    anomaly_score: Decimal | None
    created_at: datetime
    items: list[SaleItemOut]

    class Config:
        from_attributes = True
