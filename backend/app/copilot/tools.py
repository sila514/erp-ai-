"""
AI Copilot, LLM'e doğrudan veritabanı erişimi vermez.
Bunun yerine burada tanımlı, parametreli ve güvenli fonksiyonları "tool" olarak sunar.
LLM hangi fonksiyonu çağıracağına karar verir, gerçek veriyi biz çekeriz.
"""
import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.customer import Customer
from app.models.finance import FinanceTransaction, TransactionType
from app.models.product import Product
from app.models.sale import Sale

# LLM'e gönderilecek tool şemaları (Gemini Interactions API function-declaration formatı)
COPILOT_TOOLS = [
    {
        "type": "function",
        "name": "get_low_stock_products",
        "description": "Stok seviyesi yeniden sipariş eşiğinin altında veya çok yakın olan ürünleri listeler.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "get_top_at_risk_customers",
        "description": "Churn (kayıp) riski en yüksek müşterileri, risk skoruna göre sıralı listeler.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "Kaç müşteri döndürülsün"}},
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "get_finance_summary",
        "description": "Toplam gelir, gider ve net kâr özetini döndürür.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "get_recent_flagged_sales",
        "description": "Anomali olarak işaretlenmiş son satışları listeler.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "get_correlation_insights",
        "description": (
            "Churn veya talep tahmini için hangi feature'ların hedefle istatistiksel olarak "
            "anlamlı ilişkili olduğunu (çoklu test düzeltmesi sonrası) döndürür. Bu sonuçlar "
            "SADECE korelasyon/ilişkidir — nedensellik değildir, asla 'X, Y'ye sebep oluyor' "
            "gibi bir iddia kurma; 'X ile Y arasında ilişki gözlemleniyor' şeklinde ifade et."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "enum": ["churn", "demand"],
                    "description": "Hangi hedef için ilişki analizi yapılsın",
                },
                "product_id": {
                    "type": "string",
                    "description": "target='demand' ise hangi ürün için (verilmezse en çok hareket gören ürün kullanılır)",
                },
            },
            "required": ["target"],
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

    if tool_name == "get_correlation_insights":
        target = tool_input.get("target", "churn")
        params = {"product_id": tool_input["product_id"]} if tool_input.get("product_id") else {}
        try:
            resp = httpx.get(
                f"{settings.ML_SERVICE_URL}/analytics/feature-importance/{target}",
                params=params,
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            return {"error": f"ML servisinden ilişki verisi alınamadı: {exc}"}

        significant = [row for row in data["results"] if row.get("significant")]
        return {
            "target": data["target"],
            "disclaimer": data["disclaimer"],
            "significant_relationships": [
                {
                    "feature": row["feature"],
                    "correlation": row["correlation"],
                    "direction": "pozitif" if (row["correlation"] or 0) > 0 else "negatif",
                    "corrected_p_value": row["p_value_corrected"],
                }
                for row in significant
            ],
            "note": "significant_relationships boşsa, çoklu test düzeltmesi sonrası anlamlı bir ilişki bulunamadı demektir.",
        }

    return {"error": f"Bilinmeyen fonksiyon: {tool_name}"}
