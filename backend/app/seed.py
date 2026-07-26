"""
Geliştirme ortamında hızlı test için örnek veri ekler.
Önce şema migration ile kurulmuş olmalı: cd backend && alembic upgrade head
Çalıştırma: cd backend && python -m app.seed
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import *  # noqa
from app.models.customer import Customer
from app.models.finance import FinanceTransaction, TransactionType
from app.models.product import Product, StockMovement
from app.models.sale import Sale, SaleItem, SaleStatus
from app.models.user import User, UserRole

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

customers = []
for i in range(1, 21):
    c = Customer(
        name=f"Müşteri {i}",
        email=f"musteri{i}@example.com",
        lifetime_value=random.uniform(500, 20000),
    )
    db.add(c)
    customers.append(c)

db.flush()

# Geçmiş 90 gün için rastgele satışlar (dashboard trend grafikleri için)
for day_offset in range(90):
    date = datetime.utcnow() - timedelta(days=day_offset)
    for _ in range(random.randint(1, 5)):
        customer = random.choice(customers)
        items_data = [
            (random.choice(products), random.randint(1, 5)) for _ in range(random.randint(1, 3))
        ]
        total = sum(Decimal(str(p.unit_price)) * qty for p, qty in items_data)
        is_anomaly = random.random() < 0.05
        sale = Sale(
            customer_id=customer.id,
            status=SaleStatus.COMPLETED,
            total_amount=total,
            is_flagged_anomaly=is_anomaly,
            anomaly_score=round(random.uniform(0.7, 0.98), 4) if is_anomaly else None,
            created_at=date,
        )
        db.add(sale)
        db.flush()
        for product, qty in items_data:
            db.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=product.unit_price,
                )
            )

# Geçmiş 12 ay için gelir/gider işlemleri (finans özet ve grafiği için)
income_categories = ["Ürün satışı", "Hizmet geliri", "Diğer"]
expense_categories = ["Tedarik", "Personel", "Kira", "Pazarlama"]
for month_offset in range(12):
    date = datetime.utcnow() - timedelta(days=30 * month_offset)
    for _ in range(random.randint(2, 4)):
        db.add(
            FinanceTransaction(
                type=TransactionType.INCOME,
                category=random.choice(income_categories),
                amount=random.uniform(5000, 50000),
                created_at=date,
            )
        )
    for _ in range(random.randint(2, 4)):
        db.add(
            FinanceTransaction(
                type=TransactionType.EXPENSE,
                category=random.choice(expense_categories),
                amount=random.uniform(2000, 30000),
                created_at=date,
            )
        )

db.commit()
db.close()
print("Örnek veri eklendi.")
