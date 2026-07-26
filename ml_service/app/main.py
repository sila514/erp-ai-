from fastapi import FastAPI

from app.demand_forecast.router import router as demand_forecast_router
from app.stock_risk.router import router as stock_risk_router
from app.customer_segmentation.router import router as segmentation_router
from app.churn.router import router as churn_router
from app.anomaly_detection.router import router as anomaly_router

app = FastAPI(title="ERP AI - ML Service")

app.include_router(demand_forecast_router)
app.include_router(stock_risk_router)
app.include_router(segmentation_router)
app.include_router(churn_router)
app.include_router(anomaly_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ml_service"}
