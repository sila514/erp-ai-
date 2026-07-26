from app.models.customer import Customer
from app.models.sale import Sale, SaleStatus


def test_overview_counts(client, db):
    headers_client = client

    # Biri düşük stoklu, biri değil - iki ürün
    from tests.conftest import auth_headers

    headers = auth_headers(headers_client, "dash_admin", "pw123456", role="admin")
    headers_client.post(
        "/api/inventory/products",
        json={
            "sku": "LOW-1",
            "name": "Az Stoklu Ürün",
            "unit_price": "10.00",
            "unit_cost": "5.00",
            "stock_quantity": 2,
            "reorder_level": 10,
        },
        headers=headers,
    )
    headers_client.post(
        "/api/inventory/products",
        json={
            "sku": "OK-1",
            "name": "Yeterli Stoklu Ürün",
            "unit_price": "10.00",
            "unit_cost": "5.00",
            "stock_quantity": 100,
            "reorder_level": 10,
        },
        headers=headers,
    )

    customer = Customer(name="Dashboard Müşterisi")
    db.add(customer)
    db.commit()
    db.refresh(customer)

    flagged_sale = Sale(
        customer_id=customer.id,
        status=SaleStatus.COMPLETED,
        total_amount=999,
        is_flagged_anomaly=True,
        anomaly_score=0.91,
    )
    normal_sale = Sale(customer_id=customer.id, status=SaleStatus.COMPLETED, total_amount=10)
    db.add_all([flagged_sale, normal_sale])
    db.commit()

    resp = client.get("/api/dashboard/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_products"] == 2
    assert body["low_stock_products"] == 1
    assert body["total_customers"] == 1
    assert body["flagged_anomalous_sales"] == 1
