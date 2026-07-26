"""
Korelasyon / istatistiksel analiz API endpoint'leri.

KORELASYON NEDENSELLİK DEĞİLDİR: bu endpoint'lerin hiçbiri nedensellik iddiası
yapmaz — yalnızca istatistiksel ilişkiyi (korelasyon, birliktelik, bağımlılık)
raporlar. Her yanıt bu uyarıyı `disclaimer` alanında taşır.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.analytics.correlation import (
    acf_pacf_analysis,
    correlation_matrix,
    feature_target_importance,
    variance_inflation_factors,
)
from app.analytics.data_loaders import load_product_features, load_sales_features
from app.churn.feature_engineering import FEATURE_COLUMNS as CHURN_FEATURE_COLUMNS
from app.churn.feature_engineering import build_customer_features, label_churn
from app.churn.train import LABEL_HORIZON_DAYS, SNAPSHOT_LAG_DAYS
from app.common.database import get_db
from app.demand_forecast.features import FEATURE_COLUMNS as DEMAND_FEATURE_COLUMNS
from app.demand_forecast.features import build_features, load_daily_demand

router = APIRouter(prefix="/analytics", tags=["analytics"])

CAUSALITY_DISCLAIMER = "Korelasyon nedensellik değildir. Bu sonuçlar yalnızca istatistiksel ilişkiyi gösterir."


@router.get("/correlation-matrix")
def get_correlation_matrix(
    entity: str = Query(..., pattern="^(sales|customers|products)$"),
    db: Session = Depends(get_db),
):
    if entity == "sales":
        df = load_sales_features(db)
    elif entity == "products":
        df = load_product_features(db)
    else:
        df = build_customer_features(db, datetime.now(timezone.utc))

    if df.empty or df.select_dtypes(include="number").shape[1] < 2:
        raise HTTPException(status_code=422, detail="Korelasyon hesaplamak için yetersiz sayısal veri")

    result = correlation_matrix(df)
    result["vif"] = variance_inflation_factors(df)
    result["entity"] = entity
    result["disclaimer"] = CAUSALITY_DISCLAIMER
    return result


def _default_product_id(db: Session) -> str:
    row = db.execute(
        text(
            """
            SELECT product_id FROM stock_movements WHERE movement_type = 'out'
            GROUP BY product_id ORDER BY COUNT(*) DESC LIMIT 1
            """
        )
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Hiç stok hareketi bulunamadı")
    return str(row.product_id)


@router.get("/acf/{product_id}")
def get_acf(product_id: str, max_lag: int = Query(30, ge=1, le=90), db: Session = Depends(get_db)):
    raw = load_daily_demand(db, product_id)
    if raw.empty or len(raw) < max_lag * 2 + 10:
        raise HTTPException(status_code=422, detail="ACF/PACF hesaplamak için yetersiz geçmiş veri")

    result = acf_pacf_analysis(raw["qty"].values, max_lag=max_lag)
    result["product_id"] = product_id
    result["disclaimer"] = CAUSALITY_DISCLAIMER
    return result


@router.get("/feature-importance/{target}")
def get_feature_importance(target: str, product_id: str | None = None, db: Session = Depends(get_db)):
    if target not in ("churn", "demand"):
        raise HTTPException(status_code=422, detail="target 'churn' veya 'demand' olmalı")

    if target == "churn":
        snapshot_date = datetime.now(timezone.utc) - timedelta(days=SNAPSHOT_LAG_DAYS)
        features_df = build_customer_features(db, snapshot_date)
        labels_df = label_churn(db, snapshot_date, LABEL_HORIZON_DAYS)
        merged = features_df.merge(labels_df, on="customer_id", how="inner")
        if len(merged) < 20 or merged["churn"].nunique() < 2:
            raise HTTPException(status_code=422, detail="Feature importance için yetersiz churn verisi")
        X = merged[CHURN_FEATURE_COLUMNS]
        y = merged["churn"]
        result = feature_target_importance(X, y, task="classification")
        result["target"] = "churn"
    else:
        pid = product_id or _default_product_id(db)
        raw = load_daily_demand(db, pid)
        if raw.empty or len(raw) < 60:
            raise HTTPException(status_code=422, detail="Feature importance için yetersiz talep verisi")
        features = build_features(raw)
        X = features[DEMAND_FEATURE_COLUMNS]
        y = features["qty"]
        result = feature_target_importance(X, y, task="regression")
        result["target"] = "demand"
        result["product_id"] = pid

    result["disclaimer"] = CAUSALITY_DISCLAIMER
    return result
