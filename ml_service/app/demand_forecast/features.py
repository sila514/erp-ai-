"""
Stok hareketlerinden (stock_movements) günlük satış miktarına dayalı
zaman serisi feature'ları üretir. Gerçek projede bu fonksiyon,
satış kalemlerini (sale_items) de kullanarak daha zengin feature set'i çıkarmalı.
"""
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

FEATURE_COLUMNS = ["lag_1", "lag_7", "rolling_mean_7", "rolling_mean_30", "day_of_week", "day_of_month"]


def load_daily_demand(db: Session, product_id) -> pd.DataFrame:
    """Belirli bir ürün için günlük çıkış (satış) miktarlarını getirir."""
    query = text(
        """
        SELECT date_trunc('day', created_at) AS day, SUM(quantity) AS qty
        FROM stock_movements
        WHERE product_id = :product_id AND movement_type = 'out'
        GROUP BY day
        ORDER BY day
        """
    )
    rows = db.execute(query, {"product_id": str(product_id)}).fetchall()
    df = pd.DataFrame(rows, columns=["day", "qty"])
    if df.empty:
        return df

    df["day"] = pd.to_datetime(df["day"])
    df = df.set_index("day").asfreq("D", fill_value=0).reset_index()
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Lag, rolling mean ve haftanın günü feature'larını ekler."""
    df = df.copy()
    df["lag_1"] = df["qty"].shift(1)
    df["lag_7"] = df["qty"].shift(7)
    df["rolling_mean_7"] = df["qty"].rolling(7).mean()
    df["rolling_mean_30"] = df["qty"].rolling(30).mean()
    df["day_of_week"] = df["day"].dt.dayofweek
    df["day_of_month"] = df["day"].dt.day
    return df.dropna()
