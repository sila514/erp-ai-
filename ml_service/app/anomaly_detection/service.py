"""
Yeni bir satış işlemini, geçmiş işlem dağılımına göre anomali olup olmadığı
açısından skorlar. Üretimde model periyodik olarak geçmiş satışlarla
yeniden eğitilip diske kaydedilmeli; burada basitlik için her istekte
son N işlem üzerinden hızlı bir fit yapılır (küçük veri setlerinde kabul edilebilir,
büyük ölçekte training ayrı bir job'a taşınmalı).
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy import text
from sqlalchemy.orm import Session


def _get_recent_sales_features(db: Session, limit: int = 500) -> np.ndarray:
    rows = db.execute(
        text(
            """
            SELECT total_amount, EXTRACT(HOUR FROM created_at) AS hour
            FROM sales
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()
    if not rows:
        return np.array([])
    return np.array([[float(r[0]), float(r[1])] for r in rows])


def check_anomaly(db: Session, payload: dict) -> dict:
    history = _get_recent_sales_features(db)

    new_point = np.array([[payload["total_amount"], payload.get("item_count", 1)]])

    if history.shape[0] < 20:
        # Yetersiz geçmiş veri varsa anomali tespiti güvenilir değildir
        return {"is_anomaly": False, "anomaly_score": 0.0, "reason": "yetersiz_geçmiş_veri"}

    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(history)

    score = model.decision_function(new_point)[0]  # düşük skor = daha anormal
    is_anomaly = bool(model.predict(new_point)[0] == -1)

    # decision_function değerini kabaca 0-1 aralığına normalize et
    normalized_score = float(max(0.0, min(1.0, 0.5 - score)))

    return {"is_anomaly": is_anomaly, "anomaly_score": round(normalized_score, 4)}
