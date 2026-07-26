# Model Card — Müşteri Segmentasyonu

**Son güncelleme**: 2026-07-26T19:56:08.390463+00:00

## Veri
- Örneklem: 300 müşteri, RFM (recency/frequency/monetary) feature'ları.

## Yöntem
- K-Means, k=2..8 aralığında taranır; **silhouette score argmax** ile otomatik k seçilir (elbow/inertia eğrisi de hesaplanır, ama öznel olduğu için sadece bilgi amaçlıdır).
- Küme etiketleri hardcoded değildir: her kümenin z-skor merkezleri (düşük recency + yüksek frequency/monetary → sadık_müşteri; yüksek monetary + düşük tenure → yüksek_değerli; düşük frequency + düşük tenure → yeni_müşteri; yüksek recency → risk_altında) ile karşılaştırılır; eşleşmeyen kümeler `segment_N` kalır.

## Sonuçlar

| k | Silhouette | Inertia |
|---|---|---|
| 2 | 0.433 | 505.8 |
| 3 (seçilen) | 0.470 | 308.0 |
| 4 | 0.464 | 227.7 |
| 5 | 0.375 | 191.1 |
| 6 | 0.388 | 161.5 |
| 7 | 0.370 | 142.4 |
| 8 | 0.376 | 125.4 |

**Seçilen k**: 3 (silhouette=0.470)

**Otomatik atanan segment dağılımı**: {'risk_altında': 63, 'yeni_müşteri': 143, 'sadık_müşteri': 94}

## Sınırlılıklar
- Segmentasyon modeli diske kaydedilmez; her istek/rapor çalıştırıldığında canlı RFM üzerinden yeniden hesaplanır (müşteri sayısı arttıkça maliyeti gözden geçirilmeli).
- Otomatik isimlendirme z-skor eşiklerine (±0.3) dayanır; küme merkezleri bu eşiklerin hiçbirini net geçmezse `segment_N` gibi genel bir isim kalır — bu beklenen bir davranıştır.
