"""
Backend bu modül üzerinden ML servisine istek atar.
ML servisi ayrı bir FastAPI uygulaması olarak ml_service/ altında çalışır.
"""
import uuid

import httpx

from app.core.config import settings


class MLGatewayClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = base_url or settings.ML_SERVICE_URL
        self.timeout = timeout

    async def get_stock_risk(self, product_id: uuid.UUID, service_level: float = 0.95) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get(
                f"/stock-risk/{product_id}", params={"service_level": service_level}
            )
            resp.raise_for_status()
            return resp.json()

    async def get_demand_forecast(self, product_id: uuid.UUID, horizon_days: int = 30) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get(
                f"/demand-forecast/{product_id}", params={"horizon_days": horizon_days}
            )
            resp.raise_for_status()
            return resp.json()

    async def get_customer_churn(self, customer_id: uuid.UUID) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get(f"/churn/{customer_id}")
            resp.raise_for_status()
            return resp.json()

    async def get_customer_segments(self) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get("/segmentation/all")
            resp.raise_for_status()
            return resp.json()

    async def get_correlation_matrix(self, entity: str) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get("/analytics/correlation-matrix", params={"entity": entity})
            resp.raise_for_status()
            return resp.json()

    async def get_acf(self, product_id: uuid.UUID, max_lag: int = 30) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get(f"/analytics/acf/{product_id}", params={"max_lag": max_lag})
            resp.raise_for_status()
            return resp.json()

    async def get_feature_importance(self, target: str, product_id: uuid.UUID | None = None) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            params = {"product_id": str(product_id)} if product_id else {}
            resp = await client.get(f"/analytics/feature-importance/{target}", params=params)
            resp.raise_for_status()
            return resp.json()


ml_client = MLGatewayClient()
