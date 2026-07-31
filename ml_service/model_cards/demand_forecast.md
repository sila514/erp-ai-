# Model Card — Talep Tahmini (Demand Forecast)

**Son güncelleme**: 2026-07-31T10:01:13.692651+00:00
**Örnek ürün**: f8b68864-f372-48f4-ad25-e01bf72e5183

## Veri
- Kaynak: `stock_movements` tablosu, `movement_type='out'`, günlük toplanmış miktar.
- Gözlem sayısı (feature engineering sonrası): 730 gün.
- Feature'lar: lag_1, lag_7, rolling_mean_7, rolling_mean_30, day_of_week, day_of_month, month, is_weekend, is_holiday, day_of_year_sin, day_of_year_cos

## Yöntem
- Model: XGBoost regresyon, 3 ayrı quantile model (p10/p50/p90, `reg:quantileerror`).
- Değerlendirme: Expanding-window (walk-forward) time series CV, 5 katlama.
- Karşılaştırma: naive, seasonal_naive (7 gün), moving_average (7 gün) baseline'ları.
- Deney takibi: MLflow (`./mlruns`, `demand_forecast` experiment'i).

## Veri Drift Kontrolü
İlk eğitim — henüz referans dağılım yok.

## Sonuçlar (CV ortalaması)

```
Model                      MAE      RMSE    MAPE %    Fold
xgboost                   3.09      4.22      63.4       5
naive                     4.40      5.56      79.0       5
seasonal_naive            3.87      5.22      67.1       5
moving_average_7          3.42      4.38      72.9       5

XGBoost baseline'ı geçti mi: True
```

## Sınırlılıklar
- Quantile modeller her ürün için ayrı ayrı eğitilir; az sayıda geçmiş kaydı olan
  yeni ürünlerde güvenilirlik düşer (minimum ~90 gün geçmiş önerilir).
- p10/p90 aralığı XGBoost'un pinball-loss quantile regresyonundan gelir;
  kalibrasyonu (nominal %80 aralığın gerçek kapsama oranı) düzenli izlenmelidir.
- Kampanya/tatil gibi ekstrem olaylarda (eğitim verisinde az örnek) tahmin
  aralığı olduğundan dar kalabilir.
