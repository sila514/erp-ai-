from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.customer_segmentation.service import run_segmentation

router = APIRouter(prefix="/segmentation", tags=["segmentation"])


@router.get("/all")
def get_all_segments(db: Session = Depends(get_db)):
    results = run_segmentation(db)
    return {"customers": results}
