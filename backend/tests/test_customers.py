import uuid

import httpx
import respx


def test_create_and_list_customers(client):
    resp = client.post("/api/customers", json={"name": "Ayşe Yılmaz", "email": "ayse@example.com"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Ayşe Yılmaz"

    resp = client.get("/api/customers")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_churn_risk_calls_ml_service(client):
    customer = client.post("/api/customers", json={"name": "Mehmet Öz", "email": "mehmet@example.com"}).json()

    mock_response = {
        "customer_id": customer["id"],
        "churn_probability": 0.82,
        "risk_level": "high",
        "top_factors": ["uzun süredir alışveriş yok", "destek talebi arttı"],
    }
    with respx.mock(assert_all_called=True) as mock:
        mock.get(url__regex=r".*/churn/.*").mock(return_value=httpx.Response(200, json=mock_response))
        resp = client.get(f"/api/customers/{customer['id']}/churn-risk")

    assert resp.status_code == 200
    assert resp.json()["risk_level"] == "high"


def test_churn_risk_unknown_customer_404(client):
    resp = client.get(f"/api/customers/{uuid.uuid4()}/churn-risk")
    assert resp.status_code == 404


def test_segments_overview_calls_ml_service(client):
    mock_response = {"segments": [{"name": "Sadık", "count": 12}, {"name": "Risk altında", "count": 3}]}
    with respx.mock(assert_all_called=True) as mock:
        mock.get(url__regex=r".*/segmentation/all").mock(return_value=httpx.Response(200, json=mock_response))
        resp = client.get("/api/customers/segments/overview")

    assert resp.status_code == 200
    assert resp.json() == mock_response
