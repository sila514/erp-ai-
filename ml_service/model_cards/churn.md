# Model Card — Müşteri Churn Tahmini

**Son güncelleme**: 2026-07-26T19:56:47.114476+00:00
**Eğitim snapshot tarihi**: 2026-03-28T19:56:41.915947+00:00 (bugünden 120 gün önce)

## Veri
- Örneklem: 269 müşteri, churn oranı %21.9
- Etiket: snapshot tarihinden sonraki 90 gün içinde satın alma yoksa churn=1 (leakage'siz — feature'lar sadece snapshot'tan önceki veriyi kullanır).
- Feature'lar: recency_days, frequency, avg_order_value, monetary_total, trend_ratio, category_diversity, anomaly_ratio, tenure_days

## Yöntem
- 5-fold stratified cross-validation ile XGBoost ve LogisticRegression (baseline) karşılaştırıldı; üretim modeli tüm veriyle yeniden eğitildi.
- SHAP (TreeExplainer) ile birey bazlı açıklama; API yanıtındaki `top_factors` gerçek SHAP değerlerinden üretilir (bkz. `service.py`).
- Eşik: out-of-fold tahminlerden precision-recall eğrisi ile F1-maksimize eden nokta seçildi (gerçek bir iş maliyet matrisi olmadığından bu başlangıç noktasıdır).

## Sonuçlar (CV ortalaması, out-of-fold)

| Model | AUC-ROC | Precision@0.5 | Recall@0.5 |
|---|---|---|---|
| xgboost | 0.705 | 0.348 | 0.224 |
| logistic_regression | 0.686 | 0.331 | 0.747 |

**F1-optimal eşik**: 0.071 (precision=0.318, recall=0.814, f1=0.457)

## Kalibrasyon
Gözlenen vs tahmin edilen olasılık (quantile bin): [(0.056, 0.01), (0.13, 0.031), (0.264, 0.102), (0.278, 0.257), (0.37, 0.609)]

## Sınırlılıklar
- Eşik F1-optimal seçildi; gerçek iş maliyeti (yanlış pozitif/negatif maliyeti) girilirse değişmeli.
- Örneklem boyutu (~birkaç yüz müşteri) SHAP/kalibrasyon gibi tekniklerin güvenilirliğini sınırlar; üretimde müşteri sayısı arttıkça yeniden değerlendirilmeli.
- `anomaly_ratio` feature'ı şu an çoğunlukla sıfır (anomali işaretleme canlı olay akışıyla oluşur, sentetik veri seed'inde önceden etiketlenmez).
