import asyncio
import uuid

from app.core.events import SALES_STREAM_KEY
from tests.conftest import auth_headers


def _create_customer(client) -> str:
    resp = client.post("/api/customers", json={"name": "Test Müşteri", "email": "musteri@example.com"})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_product(client) -> dict:
    headers = auth_headers(client, "sales_admin", "pw123456", role="admin")
    resp = client.post(
        "/api/inventory/products",
        json={
            "sku": "SKU-100",
            "name": "Satış Ürünü",
            "unit_price": "50.00",
            "unit_cost": "20.00",
            "stock_quantity": 100,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


def test_create_sale_computes_total_and_publishes_event(client, fake_redis):
    customer_id = _create_customer(client)
    product = _create_product(client)

    resp = client.post(
        "/api/sales",
        json={
            "customer_id": customer_id,
            "items": [{"product_id": product["id"], "quantity": 2, "unit_price": "50.00"}],
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert float(body["total_amount"]) == 100.0
    # Anomali kontrolü artık senkron değil (Redis event ile ml_service'e devredildi):
    # oluşturma anında varsayılan False döner, birkaç saniye içinde güncellenir.
    assert body["is_flagged_anomaly"] is False

    stream_length = asyncio.run(fake_redis.xlen(SALES_STREAM_KEY))
    assert stream_length == 1


def test_list_sales(client):
    customer_id = _create_customer(client)
    product = _create_product(client)
    client.post(
        "/api/sales",
        json={
            "customer_id": customer_id,
            "items": [{"product_id": product["id"], "quantity": 1, "unit_price": "50.00"}],
        },
    )
    resp = client.get("/api/sales")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_unknown_sale_404(client):
    resp = client.get(f"/api/sales/{uuid.uuid4()}")
    assert resp.status_code == 404
