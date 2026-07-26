from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.churn.service import predict_churn

router = APIRouter(prefix="/churn", tags=["churn"])


@router.get("/{customer_id}")
def get_churn(customer_id: str, db: Session = Depends(get_db)):
    try:
        return predict_churn(db, customer_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
