import uuid
from decimal import Decimal

from pydantic import BaseModel, EmailStr


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None


class CustomerOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str | None
    phone: str | None
    segment: str | None
    churn_risk_score: Decimal | None
    lifetime_value: Decimal | None

    class Config:
        from_attributes = True


class ChurnRiskOut(BaseModel):
    customer_id: uuid.UUID
    churn_probability: float
    risk_level: str
    top_factors: list[str]
