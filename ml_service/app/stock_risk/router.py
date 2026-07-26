from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.stock_risk.service import compute_stock_risk

router = APIRouter(prefix="/stock-risk", tags=["stock-risk"])


@router.get("/{product_id}")
def get_stock_risk(
    product_id: str,
    service_level: float = Query(0.95, gt=0.5, lt=0.999),
    db: Session = Depends(get_db),
):
    try:
        return compute_stock_risk(db, product_id, service_level=service_level)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
