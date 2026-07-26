from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.ml_gateway.client import ml_client
from app.models.sale import Sale, SaleItem
from app.modules.sales.schemas import SaleCreate, SaleOut

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("", response_model=list[SaleOut])
def list_sales(db: Session = Depends(get_db)):
    return db.query(Sale).all()


@router.post("", response_model=SaleOut, status_code=201)
async def create_sale(payload: SaleCreate, db: Session = Depends(get_db)):
    total = sum(item.quantity * item.unit_price for item in payload.items)

    sale = Sale(customer_id=payload.customer_id, total_amount=total)
    db.add(sale)
    db.flush()  # sale.id'yi almak için commit'ten önce flush

    for item in payload.items:
        db.add(SaleItem(sale_id=sale.id, **item.model_dump()))

    # ML servisine anlık anomali kontrolü gönder (tutar, sıklık, saat gibi sinyallerle)
    anomaly_result = await ml_client.check_sale_anomaly(
        {
            "customer_id": str(payload.customer_id),
            "total_amount": float(total),
            "item_count": len(payload.items),
        }
    )
    sale.is_flagged_anomaly = anomaly_result.get("is_anomaly", False)
    sale.anomaly_score = anomaly_result.get("anomaly_score")

    db.commit()
    db.refresh(sale)
    return sale


@router.get("/{sale_id}", response_model=SaleOut)
def get_sale(sale_id, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Satış bulunamadı")
    return sale
