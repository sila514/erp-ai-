from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.stock_risk.service import compute_stock_risk

router = APIRouter(prefix="/stock-risk", tags=["stock-risk"])


@router.get("/{product_id}")
def get_stock_risk(product_id: str, db: Session = Depends(get_db)):
    try:
        return compute_stock_risk(db, product_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
