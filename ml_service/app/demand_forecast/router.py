from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.demand_forecast.predict import predict_demand

router = APIRouter(prefix="/demand-forecast", tags=["demand-forecast"])


@router.get("/{product_id}")
def get_demand_forecast(product_id: str, horizon_days: int = 30, db: Session = Depends(get_db)):
    try:
        return predict_demand(db, product_id, horizon_days)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
