import uuid

from sqlalchemy import Column, String, Numeric, Integer, DateTime, func
from app.core.types import GUID

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sku = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(128), nullable=True, index=True)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    unit_cost = Column(Numeric(12, 2), nullable=False, default=0)
    stock_quantity = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, nullable=False, default=10)
    lead_time_days = Column(Integer, nullable=False, default=7)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StockMovement(Base):
    """Stok hareketleri — talep tahmini ve stok riski modellerinin temel veri kaynağı."""

    __tablename__ = "stock_movements"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    product_id = Column(GUID(), nullable=False, index=True)
    movement_type = Column(String(16), nullable=False)  # "in" | "out" | "adjustment"
    quantity = Column(Integer, nullable=False)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
