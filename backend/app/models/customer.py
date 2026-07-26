import uuid

from sqlalchemy import Column, String, DateTime, func, Numeric
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(128), nullable=True, index=True)
    phone = Column(String(32), nullable=True)
    segment = Column(String(64), nullable=True, index=True)  # ML segmentasyon sonucu ile güncellenir
    churn_risk_score = Column(Numeric(5, 4), nullable=True)  # 0-1 arası, ML servisinden gelir
    lifetime_value = Column(Numeric(14, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
