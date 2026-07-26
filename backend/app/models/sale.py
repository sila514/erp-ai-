import enum
import uuid

from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Enum, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SaleStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Sale(Base):
    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    status = Column(Enum(SaleStatus), nullable=False, default=SaleStatus.PENDING)
    total_amount = Column(Numeric(14, 2), nullable=False, default=0)
    is_flagged_anomaly = Column(Boolean, nullable=False, default=False)  # anomali tespiti sonucu
    anomaly_score = Column(Numeric(5, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)

    sale = relationship("Sale", back_populates="items")
