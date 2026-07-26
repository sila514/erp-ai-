# Model Card — Talep Tahmini (Demand Forecast)

**Son güncelleme**: 2026-07-26T19:54:40.457071+00:00
**Örnek ürün**: 1971ee24-0e28-4f94-ae5a-bf05e98e9d56

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
PSI=0.0000 (önemli değişim yok), KS p-value=1.0000 (drifted=False)

## Sonuçlar (CV ortalaması)

```
Model                      MAE      RMSE    MAPE %    Fold
xgboost                   2.47      3.04      69.8       5
naive                     3.41      4.29      92.1       5
seasonal_naive            2.81      3.76      62.4       5
moving_average_7          2.47      3.23      72.5       5

XGBoost baseline'ı geçti mi: True
```

## Sınırlılıklar
- Quantile modeller her ürün için ayrı ayrı eğitilir; az sayıda geçmiş kaydı olan
  yeni ürünlerde güvenilirlik düşer (minimum ~90 gün geçmiş önerilir).
- p10/p90 aralığı XGBoost'un pinball-loss quantile regresyonundan gelir;
  kalibrasyonu (nominal %80 aralığın gerçek kapsama oranı) düzenli izlenmelidir.
- Kampanya/tatil gibi ekstrem olaylarda (eğitim verisinde az örnek) tahmin
  aralığı olduğundan dar kalabilir.
