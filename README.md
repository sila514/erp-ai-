# ERP AI Platform

Yapay zekâ destekli, modüler ve ölçeklenebilir ERP sistemi.
Klasik ERP modüllerine (stok, satış, müşteri, finans) ek olarak makine
öğrenmesi destekli karar araçları ve doğal dil ile çalışan bir AI Copilot içerir.

## Mimari

```
frontend (React + TS)  →  backend (FastAPI)  →  PostgreSQL
                              │        ↑              ↑
                              │        │         ml_service (FastAPI +
                              │        │          scikit-learn/XGBoost)
                              │        │
                              └── Redis Streams ───────┘
                          (sale.created event; ml_service arka planda
                           dinler, anomali skorunu hesaplayıp sonucu
                           doğrudan PostgreSQL'e yazar)
```

- **backend**: Kimlik doğrulama, ERP modülleri (stok/satış/müşteri/finans), AI Copilot
  (Anthropic tool-use ile güvenli fonksiyon çağırma). Şema Alembic migration ile yönetilir.
- **ml_service**: Ayrı bir mikroservis. Talep tahmini, stok riski, müşteri segmentasyonu,
  churn tahmini ve anomali tespiti. Redis Streams üzerinden `sale.created` olaylarını
  dinleyen bir consumer içerir (event-driven; backend artık ML sonucunu senkron beklemez).
- **frontend**: Koyu temalı (Power BI tarzı) yönetici paneli, modül sayfaları, AI Copilot
  sohbet arayüzü, recharts ile animasyonlu grafikler.

## Hızlı başlangıç (Docker ile)

```bash
cp infra/.env.example infra/.env
# infra/.env içine ANTHROPIC_API_KEY değerini ekle (Copilot için gerekli)

docker compose up --build
```

`backend` servisi ayağa kalkarken önce `alembic upgrade head` çalıştırır, sonra API'yi başlatır.

- Backend: http://localhost:8000/docs
- ML servisi: http://localhost:8001/docs
- Frontend: http://localhost:5173

## Lokal (Docker'sız) geliştirme

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../infra/.env.example .env   # DATABASE_URL / REDIS_URL'i localhost'a göre düzenle
alembic upgrade head             # şemayı kur (create_all artık kullanılmıyor)
python -m app.seed                # örnek veri ekle (opsiyonel ama önerilir)
uvicorn app.main:app --reload
```

### ML servisi
```bash
cd ml_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```
Başlarken otomatik olarak Redis Streams'teki `erp:events:sales` stream'ini bir
consumer group ile dinlemeye başlar (bkz. `app/events/consumer.py`).

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Testler ve CI

```bash
cd backend
pytest                # varsayılan: in-memory SQLite, Docker/Postgres gerekmez
TEST_DATABASE_URL=postgresql://erp_user:erp_pass@localhost:5432/erp_db pytest   # gerçek Postgres'e karşı
```

`.github/workflows/ci.yml`, her push/PR'da şunları çalıştırır: backend testleri (gerçek
Postgres service container + `alembic upgrade head`), ml_service import sağlığı, frontend
lint/build (tsc + vite), ve üç servisin de Docker imajlarının build edilebildiğinin kontrolü.

## İlk model eğitimi (talep tahmini)

Seed script ile örnek veri ekledikten sonra, en az bir ürün için modeli eğit:

```bash
cd ml_service
python -m app.demand_forecast.train <product_id>
```

`product_id`'yi backend `/api/inventory/products` endpoint'inden alabilirsin.
Model eğitilmeden `/stock-risk` ve `/demand-forecast` endpoint'leri fallback
(basit ortalama) değerler döndürür — sistem çökmez, sadece daha az isabetli tahmin yapar.

## Sıradaki adımlar

1. ML modelleri için zamanlanmış yeniden eğitim job'ları ekle (örn. Celery beat veya
   basit bir cron + script) - talep tahmini modeli şu an manuel tetikleniyor.
2. AI Copilot için tool setini genişlet (örn. "bu ürünün talep tahminini göster").
3. Auth akışını frontend'e bağla (login sayfası + token saklama) - API tarafı hazır
   (`/api/auth/register`, `/api/auth/login`, JWT), frontend henüz login ekranı içermiyor.
