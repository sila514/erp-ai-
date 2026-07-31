# Model Card — Anomali Tespiti (Satış İşlemleri)

**Son güncelleme**: 2026-07-31T10:01:17.595981+00:00

## Veri
- Geçmiş satış sayısı: 5000
- Feature'lar: total_amount, item_count, hour_of_day, is_weekend
- Değerlendirme seti: gerçek verinin %30'luk tutma payına 40 sentetik aykırı nokta enjekte edilerek oluşturuldu (total_amount/item_count 4-15x büyütülerek — yalnızca değerlendirme amaçlı, gerçek veritabanına yazılmaz).

## Yöntem
- Sıralama kalitesi: decision_function skorlarına göre en anormal 40 nokta içindeki gerçek (enjekte edilmiş) anomali oranı — **precision@k** (contamination'dan bağımsız bir metrik, çünkü contamination sadece predict()'in ikili eşiğini belirler).
- `contamination`, her adayın kendi predict() eşiğinde ölçülen precision/recall/F1 taranarak (F1-argmax) seçildi.
- Üretim modeli, seçilen contamination ile TÜM geçmiş veride yeniden eğitilip diske kaydedildi (`anomaly_model.joblib`); canlı skorlama artık her istekte yeniden fit etmez.

## Sonuçlar

**Sıralama kalitesi — precision@40**: 0.800

| Contamination | Precision | Recall | F1 |
|---|---|---|---|
| 0.01 (seçilen) | 0.653 | 0.800 | 0.719 |
| 0.02 | 0.525 | 0.800 | 0.634 |
| 0.05 | 0.330 | 0.925 | 0.487 |
| 0.08 | 0.224 | 0.950 | 0.362 |
| 0.12 | 0.165 | 0.950 | 0.281 |
| 0.18 | 0.121 | 0.950 | 0.215 |

**Seçilen contamination**: 0.01

## Sınırlılıklar
- Değerlendirme etiketleri sentetik enjeksiyonla üretilmiştir; gerçek dolandırıcılık/hata örüntüleri farklı görünebilir, üretimde gerçek işaretlenmiş vakalar biriktikçe yeniden değerlendirilmelidir.
- Model periyodik olarak (örn. haftalık) yeniden eğitilmelidir; bu script bir zamanlanmış job'a bağlanmalıdır.
