"""
Geliştirme ortamında hızlı test için örnek veri ekler.
Çalıştırma: cd backend && python -m app.seed
"""
import random
from datetime import datetime, timedelta

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import *  # noqa
from app.models.customer import Customer
from app.models.product import Product, StockMovement
from app.models.user import User, UserRole

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if not db.query(User).filter(User.username == "admin").first():
    db.add(
        User(
            username="admin",
            email="admin@example.com",
            full_name="Sistem Yöneticisi",
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN,
        )
    )

products = []
for i in range(1, 11):
    p = Product(
        sku=f"SKU-{i:03d}",
        name=f"Ürün {i}",
        category=random.choice(["Elektronik", "Gıda", "Tekstil"]),
        unit_price=random.uniform(50, 500),
        unit_cost=random.uniform(20, 300),
        stock_quantity=random.randint(0, 100),
        reorder_level=20,
        lead_time_days=7,
    )
    db.add(p)
    products.append(p)

db.flush()

# Geçmiş 60 gün için rastgele stok çıkış hareketleri (talep tahmini modelinin eğitilebilmesi için)
for p in products:
    for day_offset in range(60):
        date = datetime.utcnow() - timedelta(days=day_offset)
        qty = random.randint(0, 8)
        if qty > 0:
            db.add(
                StockMovement(
                    product_id=p.id,
                    movement_type="out",
                    quantity=qty,
                    created_at=date,
                )
            )

for i in range(1, 21):
    db.add(
        Customer(
            name=f"Müşteri {i}",
            email=f"musteri{i}@example.com",
        )
    )

db.commit()
db.close()
print("Örnek veri eklendi.")
