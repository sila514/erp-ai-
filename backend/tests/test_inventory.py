import httpx
import respx

from tests.conftest import auth_headers

PRODUCT_PAYLOAD = {
    "sku": "SKU-001",
    "name": "Test Ürünü",
    "category": "Elektronik",
    "unit_price": "199.90",
    "unit_cost": "120.00",
    "stock_quantity": 5,
    "reorder_level": 10,
}


def test_create_product_requires_role(client):
    headers = auth_headers(client, "sales_user", "pw123456", role="sales")
    resp = client.post("/api/inventory/products", json=PRODUCT_PAYLOAD, headers=headers)
    assert resp.status_code == 403


def test_create_and_list_products(client):
    headers = auth_headers(client, "inv_admin", "pw123456", role="admin")
    resp = client.post("/api/inventory/products", json=PRODUCT_PAYLOAD, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["sku"] == "SKU-001"

    resp = client.get("/api/inventory/products")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_duplicate_sku_rejected(client):
    headers = auth_headers(client, "inv_admin2", "pw123456", role="admin")
    client.post("/api/inventory/products", json=PRODUCT_PAYLOAD, headers=headers)
    resp = client.post("/api/inventory/products", json=PRODUCT_PAYLOAD, headers=headers)
    assert resp.status_code == 400


def test_stock_risk_calls_ml_service(client):
    headers = auth_headers(client, "inv_admin3", "pw123456", role="admin")
    product = client.post("/api/inventory/products", json=PRODUCT_PAYLOAD, headers=headers).json()

    mock_response = {
        "product_id": product["id"],
        "current_stock": 5,
        "predicted_daily_demand": 1.2,
        "daily_demand_sigma": 0.5,
        "days_until_stockout": 4.1,
        "risk_level": "high",
        "service_level": 0.95,
        "safety_stock": 3.2,
        "reorder_point": 12.5,
        "recommended_reorder_quantity": 30,
        "uncertainty_source": "quantile_forecast",
    }

    with respx.mock(assert_all_called=True) as mock:
        mock.get(url__regex=r".*/stock-risk/.*").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        resp = client.get(f"/api/inventory/products/{product['id']}/stock-risk")

    assert resp.status_code == 200
    assert resp.json()["risk_level"] == "high"


def test_get_unknown_product_404(client):
    import uuid

    resp = client.get(f"/api/inventory/products/{uuid.uuid4()}")
    assert resp.status_code == 404
