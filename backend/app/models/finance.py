import enum
import uuid

from sqlalchemy import Column, String, Numeric, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class FinanceTransaction(Base):
    __tablename__ = "finance_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(TransactionType), nullable=False)
    category = Column(String(128), nullable=True, index=True)
    amount = Column(Numeric(14, 2), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
