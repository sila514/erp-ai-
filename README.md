# ERP AI Platform

Yapay zekâ destekli, modüler ve ölçeklenebilir ERP sistemi.
Klasik ERP modüllerine (stok, satış, müşteri, finans) ek olarak makine
öğrenmesi destekli karar araçları ve doğal dil ile çalışan bir AI Copilot içerir.

## Mimari

```
frontend (React + TS)  →  backend (FastAPI)  →  PostgreSQL
                              ↓        ↑
                         ml_service (FastAPI + scikit-learn/XGBoost)
```

- **backend**: Kimlik doğrulama, ERP modülleri (stok/satış/müşteri/finans), AI Copilot
  (Anthropic tool-use ile güvenli fonksiyon çağırma).
- **ml_service**: Ayrı bir mikroservis. Talep tahmini, stok riski, müşteri segmentasyonu,
  churn tahmini ve anomali tespiti.
- **frontend**: Yönetici paneli, modül sayfaları, AI Copilot sohbet arayüzü.

## Hızlı başlangıç (Docker ile)

```bash
cp infra/.env.example infra/.env
# infra/.env içine ANTHROPIC_API_KEY değerini ekle (Copilot için gerekli)

docker compose up --build
```

- Backend: http://localhost:8000/docs
- ML servisi: http://localhost:8001/docs
- Frontend: http://localhost:5173

## Lokal (Docker'sız) geliştirme

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../infra/.env.example .env   # DATABASE_URL'i localhost'a göre düzenle
python -m app.seed               # örnek veri ekle (opsiyonel ama önerilir)
uvicorn app.main:app --reload
```

### ML servisi
```bash
cd ml_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

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

1. `backend/app/models` altındaki şemaya göre Alembic migration kur (şu an `create_all`
   ile otomatik oluşturuluyor, üretimde bu kapatılmalı).
2. `sales`, `customers`, `finance` frontend sayfalarını `inventory` sayfasındaki
   şablona göre tamamla.
3. ML modelleri için zamanlanmış yeniden eğitim job'ları ekle (Celery + Redis veya
   basit bir cron + script).
4. AI Copilot için tool setini genişlet (örn. "bu ürünün talep tahminini göster").
5. Auth akışını frontend'e bağla (login sayfası + token saklama).
