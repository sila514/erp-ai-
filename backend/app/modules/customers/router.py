import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.ml_gateway.client import ml_client
from app.models.customer import Customer
from app.modules.customers.schemas import ChurnRiskOut, CustomerCreate, CustomerOut

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).all()


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}/churn-risk", response_model=ChurnRiskOut)
async def get_churn_risk(customer_id: uuid.UUID, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")

    result = await ml_client.get_customer_churn(customer_id)
    return result


@router.get("/segments/overview")
async def get_segments_overview():
    """Tüm müşteri segmentlerinin (K-Means / RFM) özetini ML servisinden getirir."""
    return await ml_client.get_customer_segments()
