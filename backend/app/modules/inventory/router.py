import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.ml_gateway.client import ml_client
from app.models.product import Product
from app.modules.inventory.schemas import ProductCreate, ProductOut, StockRiskOut

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "manager", "inventory")),
):
    existing = db.query(Product).filter(Product.sku == payload.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu SKU zaten kayıtlı")

    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return product


@router.get("/products/{product_id}/stock-risk", response_model=StockRiskOut)
async def get_product_stock_risk(
    product_id: uuid.UUID,
    service_level: float = Query(0.95, gt=0.5, lt=0.999),
    db: Session = Depends(get_db),
):
    """
    ML servisinden bu ürünün stok tükenme riski tahminini alır.
    ML servisi: talep tahmininin p10/p90 belirsizlik aralığından günlük
    sigma'yı tahmin eder, `service_level`'a göre güvenlik stoğu hesaplar.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    risk = await ml_client.get_stock_risk(product_id, service_level=service_level)
    return risk
