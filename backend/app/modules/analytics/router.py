"""
Korelasyon / istatistiksel analiz endpoint'leri — ML servisindeki
`app/analytics/` modülüne proxy. Yanıt şekli entity/hedefe göre değiştiği
(farklı sayıda sütun/feature) için sabit bir Pydantic response_model
kullanılmıyor — `segments/overview` ile aynı desen.
"""
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.ml_gateway.client import ml_client

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/correlation-matrix")
async def get_correlation_matrix(entity: str = Query(..., pattern="^(sales|customers|products)$")):
    return await ml_client.get_correlation_matrix(entity)


@router.get("/acf/{product_id}")
async def get_acf(product_id: uuid.UUID, max_lag: int = Query(30, ge=1, le=90)):
    return await ml_client.get_acf(product_id, max_lag=max_lag)


@router.get("/feature-importance/{target}")
async def get_feature_importance(target: str, product_id: uuid.UUID | None = None):
    if target not in ("churn", "demand"):
        raise HTTPException(status_code=422, detail="target 'churn' veya 'demand' olmalı")
    return await ml_client.get_feature_importance(target, product_id=product_id)
