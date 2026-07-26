from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.inventory.router import router as inventory_router
from app.modules.sales.router import router as sales_router
from app.modules.customers.router import router as customers_router
from app.modules.finance.router import router as finance_router
from app.modules.dashboard.router import router as dashboard_router
from app.copilot.router import router as copilot_router

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(inventory_router)
app.include_router(sales_router)
app.include_router(customers_router)
app.include_router(finance_router)
app.include_router(dashboard_router)
app.include_router(copilot_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
