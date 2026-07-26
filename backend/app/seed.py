"""
Geliştirme ortamında ML/istatistik katmanının öğrenebileceği gerçekçi bir sentetik
veri seti üretir: trend + haftalık mevsimsellik + yıllık döngü + kampanya
sıçramaları + tatil etkisi + gürültü içeren 2 yıllık talep serileri, arketip
tabanlı (loyal/new/at_risk/churning) müşteri satın alma davranışı.

Önce şema migration ile kurulmuş olmalı: cd backend && alembic upgrade head
Çalıştırma: cd backend && python -m app.seed
"""
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import numpy as np
from sqlalchemy import insert

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.customer import Customer
from app.models.finance import FinanceTransaction, TransactionType
from app.models.product import Product, StockMovement
from app.models.sale import Sale, SaleItem, SaleStatus
from app.models.user import User, UserRole
from app.seed_data.calendar_effects import generate_campaign_calendar
from app.seed_data.customer_behavior import build_customer_profile, daily_purchase_probability
from app.seed_data.demand_generator import generate_daily_demand, sample_product_demand_profile

SEED = 42
N_DAYS = 730  # 2 yıl
N_PRODUCTS = 30
N_CUSTOMERS = 300
CATEGORIES = ["Elektronik", "Gıda", "Tekstil", "Kozmetik", "Ev & Yaşam"]

rng = np.random.default_rng(SEED)

START_DATE = date.today() - timedelta(days=N_DAYS - 1)


def dt_at(day_index: int, hour: int | None = None) -> datetime:
    d = START_DATE + timedelta(days=day_index)
    h = hour if hour is not None else int(rng.integers(8, 21))
    return datetime.combine(d, time(hour=h, minute=int(rng.integers(0, 60))))


def main() -> None:
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
        db.flush()

    campaigns = generate_campaign_calendar(N_DAYS, rng)
    print(f"Kampanya takvimi: {len(campaigns)} kampanya olayı üretildi.")

    # ---------------------------------------------------------------- ürünler
    products: list[Product] = []
    product_demand_series: dict[uuid.UUID, list[int]] = {}

    for i in range(1, N_PRODUCTS + 1):
        category = CATEGORIES[(i - 1) % len(CATEGORIES)]
        profile = sample_product_demand_profile(category, rng)
        demand = generate_daily_demand(START_DATE, N_DAYS, profile, campaigns, rng)

        recent_avg_demand = float(np.mean(demand[-30:])) if demand else 1.0
        lead_time_days = int(rng.integers(3, 15))
        reorder_level = max(5, round(recent_avg_demand * lead_time_days * 1.2))
        stock_quantity = max(0, round(recent_avg_demand * lead_time_days * rng.uniform(1.0, 2.2)))

        price_ranges = {
            "Elektronik": (300, 3500),
            "Gıda": (15, 180),
            "Tekstil": (80, 900),
            "Kozmetik": (60, 650),
            "Ev & Yaşam": (100, 1200),
        }
        lo, hi = price_ranges.get(category, (50, 500))
        unit_price = float(rng.uniform(lo, hi))
        unit_cost = unit_price * float(rng.uniform(0.45, 0.75))

        p = Product(
            id=uuid.uuid4(),
            sku=f"SKU-{i:03d}",
            name=f"{category} Ürünü {i}",
            category=category,
            unit_price=round(unit_price, 2),
            unit_cost=round(unit_cost, 2),
            stock_quantity=stock_quantity,
            reorder_level=reorder_level,
            lead_time_days=lead_time_days,
        )
        db.add(p)
        products.append(p)
        product_demand_series[p.id] = demand

    db.flush()
    print(f"{len(products)} ürün oluşturuldu.")

    # -------------------------------------------------------- stok hareketleri
    stock_movement_rows = []
    for p in products:
        demand = product_demand_series[p.id]
        running_since_restock = 0
        for t, qty in enumerate(demand):
            if qty > 0:
                stock_movement_rows.append(
                    {
                        "id": uuid.uuid4(),
                        "product_id": p.id,
                        "movement_type": "out",
                        "quantity": qty,
                        "note": None,
                        "created_at": dt_at(t),
                    }
                )
            running_since_restock += qty
            # ~3 haftada bir yeniden stoklama (gerçekçilik için)
            if t > 0 and t % 21 == 0 and running_since_restock > 0:
                stock_movement_rows.append(
                    {
                        "id": uuid.uuid4(),
                        "product_id": p.id,
                        "movement_type": "in",
                        "quantity": int(running_since_restock * 1.15) + 1,
                        "note": "Periyodik yeniden stoklama",
                        "created_at": dt_at(t, hour=9),
                    }
                )
                running_since_restock = 0

    if stock_movement_rows:
        db.execute(insert(StockMovement), stock_movement_rows)
    print(f"{len(stock_movement_rows)} stok hareketi eklendi.")

    # ------------------------------------------------------------- müşteriler
    customers: list[Customer] = []
    customer_profiles = {}
    for i in range(1, N_CUSTOMERS + 1):
        profile = build_customer_profile(rng, N_DAYS)
        signup_dt = dt_at(profile.signup_offset_days, hour=int(rng.integers(9, 18)))
        c = Customer(
            id=uuid.uuid4(),
            name=f"Müşteri {i}",
            email=f"musteri{i}@example.com",
            segment=None,
            churn_risk_score=None,
            lifetime_value=0,
            created_at=signup_dt,
        )
        db.add(c)
        customers.append(c)
        customer_profiles[c.id] = profile

    db.flush()
    print(f"{len(customers)} müşteri oluşturuldu (arketip dağılımı üretildi).")

    # ------------------------------------------------------------------ satışlar
    sale_rows = []
    sale_item_rows = []
    customer_ltv: dict[uuid.UUID, float] = defaultdict(float)
    monthly_sales_amount: dict[tuple[int, int], float] = defaultdict(float)
    monthly_sales_qty: dict[tuple[int, int], int] = defaultdict(int)

    product_ids = [p.id for p in products]
    products_by_id = {p.id: p for p in products}

    for t in range(N_DAYS):
        d = START_DATE + timedelta(days=t)
        month_key = (d.year, d.month)
        for c in customers:
            profile = customer_profiles[c.id]
            prob = daily_purchase_probability(profile, t, N_DAYS)
            if prob <= 0 or rng.random() >= prob:
                continue

            n_items = int(rng.integers(1, 4))
            chosen_product_ids = rng.choice(product_ids, size=min(n_items, len(product_ids)), replace=False)

            is_bulk_outlier = rng.random() < 0.003
            sale_id = uuid.uuid4()
            sale_total = Decimal("0")
            created_at = dt_at(t)

            items_for_sale = []
            for pid in chosen_product_ids:
                product = products_by_id[pid]
                base_qty = max(1, round(rng.uniform(1, 3) * profile.avg_basket_size))
                qty = base_qty * (rng.integers(5, 10) if is_bulk_outlier else 1)
                unit_price = Decimal(str(product.unit_price))
                sale_total += unit_price * qty
                items_for_sale.append(
                    {
                        "id": uuid.uuid4(),
                        "sale_id": sale_id,
                        "product_id": pid,
                        "quantity": int(qty),
                        "unit_price": product.unit_price,
                    }
                )

            sale_rows.append(
                {
                    "id": sale_id,
                    "customer_id": c.id,
                    "status": SaleStatus.COMPLETED,
                    "total_amount": sale_total,
                    "is_flagged_anomaly": False,
                    "anomaly_score": None,
                    "created_at": created_at,
                }
            )
            sale_item_rows.extend(items_for_sale)

            customer_ltv[c.id] += float(sale_total)
            monthly_sales_amount[month_key] += float(sale_total)
            monthly_sales_qty[month_key] += sum(i["quantity"] for i in items_for_sale)

    if sale_rows:
        db.execute(insert(Sale), sale_rows)
    if sale_item_rows:
        db.execute(insert(SaleItem), sale_item_rows)
    print(f"{len(sale_rows)} satış, {len(sale_item_rows)} satış kalemi eklendi.")

    for c in customers:
        c.lifetime_value = round(customer_ltv.get(c.id, 0.0), 2)
    db.flush()

    # -------------------------------------------------------------- finans
    finance_rows = []
    avg_unit_cost = float(np.mean([p.unit_cost for p in products])) if products else 100.0

    months = sorted(monthly_sales_amount.keys()) or [(START_DATE.year, START_DATE.month)]
    for month_idx, (year, month) in enumerate(months):
        month_start = date(year, month, 1)
        created_at = datetime.combine(month_start, time(hour=10))

        sales_amount = monthly_sales_amount.get((year, month), 0.0)
        sales_qty = monthly_sales_qty.get((year, month), 0)

        finance_rows.append(
            {
                "id": uuid.uuid4(),
                "type": TransactionType.INCOME,
                "category": "Ürün satışı",
                "amount": round(sales_amount, 2),
                "description": "Aylık toplam ürün satış geliri",
                "created_at": created_at,
            }
        )
        service_income = float(rng.uniform(3000, 9000)) * (1 + 0.15 * np.sin(2 * np.pi * month / 12))
        finance_rows.append(
            {
                "id": uuid.uuid4(),
                "type": TransactionType.INCOME,
                "category": "Hizmet geliri",
                "amount": round(max(service_income, 500), 2),
                "description": None,
                "created_at": created_at,
            }
        )

        finance_rows.append(
            {
                "id": uuid.uuid4(),
                "type": TransactionType.EXPENSE,
                "category": "Kira",
                "amount": round(float(rng.uniform(8000, 12000)), 2),
                "description": None,
                "created_at": created_at,
            }
        )
        personnel_base = 15000 * (1 + 0.01 * month_idx)  # yavaş büyüyen ekip maliyeti
        finance_rows.append(
            {
                "id": uuid.uuid4(),
                "type": TransactionType.EXPENSE,
                "category": "Personel",
                "amount": round(personnel_base * float(rng.uniform(0.95, 1.05)), 2),
                "description": None,
                "created_at": created_at,
            }
        )
        cogs = sales_qty * avg_unit_cost * float(rng.uniform(0.9, 1.1))
        finance_rows.append(
            {
                "id": uuid.uuid4(),
                "type": TransactionType.EXPENSE,
                "category": "Tedarik",
                "amount": round(max(cogs, 500), 2),
                "description": "Satılan ürünlerin tedarik maliyeti",
                "created_at": created_at,
            }
        )
        finance_rows.append(
            {
                "id": uuid.uuid4(),
                "type": TransactionType.EXPENSE,
                "category": "Pazarlama",
                "amount": round(float(rng.uniform(1500, 4000)), 2),
                "description": "Aylık taban pazarlama harcaması",
                "created_at": created_at,
            }
        )

    # Kampanya öncesi pazarlama harcaması sıçraması (kampanyadan ~5-8 gün önce
    # kaydedilir; bu, Faz 8'deki çapraz korelasyon/lag analizinin bulacağı
    # gerçek, gecikmeli "pazarlama -> satış" ilişkisini oluşturur).
    for campaign in campaigns:
        lag_days = int(rng.integers(5, 9))
        spend_day = max(0, campaign.start_day_index - lag_days)
        finance_rows.append(
            {
                "id": uuid.uuid4(),
                "type": TransactionType.EXPENSE,
                "category": "Pazarlama",
                "amount": round(2500 * campaign.intensity * float(rng.uniform(0.8, 1.2)), 2),
                "description": "Kampanya öncesi pazarlama harcaması",
                "created_at": dt_at(spend_day, hour=11),
            }
        )

    if finance_rows:
        db.execute(insert(FinanceTransaction), finance_rows)
    print(f"{len(finance_rows)} finans işlemi eklendi.")

    db.commit()
    db.close()
    print("Sentetik veri seti başarıyla oluşturuldu.")


if __name__ == "__main__":
    main()
