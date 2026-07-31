# Model Card — Müşteri Churn Tahmini

**Son güncelleme**: 2026-07-31T10:01:16.319852+00:00
**Eğitim snapshot tarihi**: 2026-04-02T10:01:13.694370+00:00 (bugünden 120 gün önce)

## Veri
- Örneklem: 269 müşteri, churn oranı %23.4
- Etiket: snapshot tarihinden sonraki 90 gün içinde satın alma yoksa churn=1 (leakage'siz — feature'lar sadece snapshot'tan önceki veriyi kullanır).
- Feature'lar: recency_days, frequency, avg_order_value, monetary_total, trend_ratio, category_diversity, anomaly_ratio, tenure_days

## Yöntem
- 5-fold stratified cross-validation ile XGBoost ve LogisticRegression (baseline) karşılaştırıldı; üretim modeli tüm veriyle yeniden eğitildi.
- SHAP (TreeExplainer) ile birey bazlı açıklama; API yanıtındaki `top_factors` gerçek SHAP değerlerinden üretilir (bkz. `service.py`).
- Eşik: out-of-fold tahminlerden precision-recall eğrisi ile F1-maksimize eden nokta seçildi (gerçek bir iş maliyet matrisi olmadığından bu başlangıç noktasıdır).

## Sonuçlar (CV ortalaması, out-of-fold)

| Model | AUC-ROC | Precision@0.5 | Recall@0.5 |
|---|---|---|---|
| xgboost | 0.714 | 0.483 | 0.282 |
| logistic_regression | 0.666 | 0.354 | 0.731 |

**F1-optimal eşik**: 0.257 (precision=0.440, recall=0.587, f1=0.503)

## Kalibrasyon
Gözlenen vs tahmin edilen olasılık (quantile bin): [(0.074, 0.013), (0.185, 0.047), (0.132, 0.115), (0.333, 0.278), (0.444, 0.625)]

## Sınırlılıklar
- Eşik F1-optimal seçildi; gerçek iş maliyeti (yanlış pozitif/negatif maliyeti) girilirse değişmeli.
- Örneklem boyutu (~birkaç yüz müşteri) SHAP/kalibrasyon gibi tekniklerin güvenilirliğini sınırlar; üretimde müşteri sayısı arttıkça yeniden değerlendirilmeli.
- `anomaly_ratio` feature'ı şu an çoğunlukla sıfır (anomali işaretleme canlı olay akışıyla oluşur, sentetik veri seed'inde önceden etiketlenmez).
