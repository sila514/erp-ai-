"""
AI Copilot, LLM'e doğrudan veritabanı erişimi vermez.
Bunun yerine burada tanımlı, parametreli ve güvenli fonksiyonları "tool" olarak sunar.
LLM hangi fonksiyonu çağıracağına karar verir, gerçek veriyi biz çekeriz.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.finance import FinanceTransaction, TransactionType
from app.models.product import Product
from app.models.sale import Sale

# Claude'a gönderilecek tool şemaları (Anthropic tool-use formatı)
COPILOT_TOOLS = [
    {
        "name": "get_low_stock_products",
        "description": "Stok seviyesi yeniden sipariş eşiğinin altında veya çok yakın olan ürünleri listeler.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_top_at_risk_customers",
        "description": "Churn (kayıp) riski en yüksek müşterileri, risk skoruna göre sıralı listeler.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "Kaç müşteri döndürülsün"}},
            "required": [],
        },
    },
    {
        "name": "get_finance_summary",
        "description": "Toplam gelir, gider ve net kâr özetini döndürür.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_recent_flagged_sales",
        "description": "Anomali olarak işaretlenmiş son satışları listeler.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
            "required": [],
        },
    },
]


def execute_tool(db: Session, tool_name: str, tool_input: dict) -> dict:
    """LLM'in seçtiği fonksiyonu gerçekten çalıştırır."""

    if tool_name == "get_low_stock_products":
        products = db.query(Product).filter(Product.stock_quantity <= Product.reorder_level).all()
        return {
            "products": [
                {"sku": p.sku, "name": p.name, "stock": p.stock_quantity, "reorder_level": p.reorder_level}
                for p in products
            ]
        }

    if tool_name == "get_top_at_risk_customers":
        limit = tool_input.get("limit", 5)
        customers = (
            db.query(Customer)
            .filter(Customer.churn_risk_score.isnot(None))
            .order_by(Customer.churn_risk_score.desc())
            .limit(limit)
            .all()
        )
        return {
            "customers": [
                {"name": c.name, "churn_risk_score": float(c.churn_risk_score)} for c in customers
            ]
        }

    if tool_name == "get_finance_summary":
        income = (
            db.query(func.coalesce(func.sum(FinanceTransaction.amount), 0))
            .filter(FinanceTransaction.type == TransactionType.INCOME)
            .scalar()
        )
        expense = (
            db.query(func.coalesce(func.sum(FinanceTransaction.amount), 0))
            .filter(FinanceTransaction.type == TransactionType.EXPENSE)
            .scalar()
        )
        return {"total_income": float(income), "total_expense": float(expense), "net_profit": float(income - expense)}

    if tool_name == "get_recent_flagged_sales":
        limit = tool_input.get("limit", 10)
        sales = (
            db.query(Sale)
            .filter(Sale.is_flagged_anomaly.is_(True))
            .order_by(Sale.created_at.desc())
            .limit(limit)
            .all()
        )
        return {
            "sales": [
                {"id": str(s.id), "total_amount": float(s.total_amount), "anomaly_score": float(s.anomaly_score or 0)}
                for s in sales
            ]
        }

    return {"error": f"Bilinmeyen fonksiyon: {tool_name}"}
