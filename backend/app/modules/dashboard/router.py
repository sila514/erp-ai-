from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Product
from app.models.sale import Sale
from app.models.customer import Customer

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    """
    Yönetici paneli için tek seferde özet veri.
    Gerçek projede burada ML servisinden toplu içgörüler de (en riskli ürünler,
    en yüksek churn riskine sahip müşteriler, son anomaliler) çekilip birleştirilir.
    """
    total_products = db.query(func.count(Product.id)).scalar()
    low_stock_products = (
        db.query(func.count(Product.id)).filter(Product.stock_quantity <= Product.reorder_level).scalar()
    )
    total_customers = db.query(func.count(Customer.id)).scalar()
    flagged_sales = db.query(func.count(Sale.id)).filter(Sale.is_flagged_anomaly.is_(True)).scalar()

    return {
        "total_products": total_products,
        "low_stock_products": low_stock_products,
        "total_customers": total_customers,
        "flagged_anomalous_sales": flagged_sales,
    }
