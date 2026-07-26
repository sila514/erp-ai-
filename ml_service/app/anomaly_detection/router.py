from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.anomaly_detection.service import check_anomaly

router = APIRouter(prefix="/anomaly", tags=["anomaly"])


class SalePayload(BaseModel):
    customer_id: str
    total_amount: float
    item_count: int = 1


@router.post("/check")
def post_check_anomaly(payload: SalePayload, db: Session = Depends(get_db)):
    return check_anomaly(db, payload.model_dump())
