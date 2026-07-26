"""
Stok hareketlerinden (stock_movements) günlük satış miktarına dayalı
zaman serisi feature'ları üretir: lag/rolling istatistikler + gerçek takvim
feature'ları (hafta günü, hafta sonu, tatil, yıl içi döngüsellik).
"""
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.common.calendar import cyclical_day_of_year, is_holiday, is_weekend

FEATURE_COLUMNS = [
    "lag_1",
    "lag_7",
    "rolling_mean_7",
    "rolling_mean_30",
    "day_of_week",
    "day_of_month",
    "month",
    "is_weekend",
    "is_holiday",
    "day_of_year_sin",
    "day_of_year_cos",
]


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


def calendar_features_for_date(d) -> dict:
    """Tek bir tarih için takvim feature'larını hesaplar (predict.py'nin recursive
    forecast döngüsünde her adımda gerçek tarihten çağrılması için)."""
    day = d.date() if hasattr(d, "date") else d
    sin_doy, cos_doy = cyclical_day_of_year(day)
    return {
        "day_of_week": day.weekday(),
        "day_of_month": day.day,
        "month": day.month,
        "is_weekend": int(is_weekend(day)),
        "is_holiday": int(is_holiday(day)),
        "day_of_year_sin": sin_doy,
        "day_of_year_cos": cos_doy,
    }


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Lag, rolling mean ve takvim feature'larını ekler."""
    df = df.copy()
    df["lag_1"] = df["qty"].shift(1)
    df["lag_7"] = df["qty"].shift(7)
    df["rolling_mean_7"] = df["qty"].rolling(7).mean()
    df["rolling_mean_30"] = df["qty"].rolling(30).mean()

    cal = df["day"].apply(calendar_features_for_date).apply(pd.Series)
    df = pd.concat([df, cal], axis=1)

    return df.dropna().reset_index(drop=True)
