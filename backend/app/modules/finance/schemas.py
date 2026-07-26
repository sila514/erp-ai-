import uuid
from decimal import Decimal

from pydantic import BaseModel

from app.models.finance import TransactionType


class TransactionCreate(BaseModel):
    type: TransactionType
    category: str | None = None
    amount: Decimal
    description: str | None = None


class TransactionOut(BaseModel):
    id: uuid.UUID
    type: TransactionType
    category: str | None
    amount: Decimal
    description: str | None

    class Config:
        from_attributes = True


class FinanceSummaryOut(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net_profit: Decimal
