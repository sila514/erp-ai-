"""
copilot/tools.py::execute_tool fonksiyonlarını doğrudan (LLM'i mock'lamadan)
test eder. Gerçek Gemini API çağrısı gerektiren tam /api/copilot/ask akışı
kapsam dışıdır (bkz. plan dokümanı) - burada test edilen, LLM'in çağırabileceği
gerçek veri erişim fonksiyonlarının doğruluğudur.
"""
import httpx
import respx

from app.copilot.tools import execute_tool
from app.models.customer import Customer
from app.models.finance import FinanceTransaction, TransactionType
from app.models.product import Product
from app.models.sale import Sale, SaleStatus


def test_get_low_stock_products(db):
    db.add(Product(sku="A1", name="Az Stok", unit_price=10, unit_cost=5, stock_quantity=1, reorder_level=10))
    db.add(Product(sku="A2", name="Yeterli Stok", unit_price=10, unit_cost=5, stock_quantity=50, reorder_level=10))
    db.commit()

    result = execute_tool(db, "get_low_stock_products", {})
    assert len(result["products"]) == 1
    assert result["products"][0]["sku"] == "A1"


def test_get_top_at_risk_customers(db):
    db.add(Customer(name="Düşük Risk", churn_risk_score=0.1))
    db.add(Customer(name="Yüksek Risk", churn_risk_score=0.9))
    db.commit()

    result = execute_tool(db, "get_top_at_risk_customers", {"limit": 1})
    assert len(result["customers"]) == 1
    assert result["customers"][0]["name"] == "Yüksek Risk"


def test_get_finance_summary(db):
    db.add(FinanceTransaction(type=TransactionType.INCOME, amount=1000))
    db.add(FinanceTransaction(type=TransactionType.EXPENSE, amount=400))
    db.commit()

    result = execute_tool(db, "get_finance_summary", {})
    assert result["total_income"] == 1000.0
    assert result["total_expense"] == 400.0
    assert result["net_profit"] == 600.0


def test_get_recent_flagged_sales(db):
    customer = Customer(name="Test")
    db.add(customer)
    db.commit()
    db.refresh(customer)

    db.add(
        Sale(
            customer_id=customer.id,
            status=SaleStatus.COMPLETED,
            total_amount=500,
            is_flagged_anomaly=True,
            anomaly_score=0.8,
        )
    )
    db.add(Sale(customer_id=customer.id, status=SaleStatus.COMPLETED, total_amount=50))
    db.commit()

    result = execute_tool(db, "get_recent_flagged_sales", {"limit": 5})
    assert len(result["sales"]) == 1
    assert result["sales"][0]["anomaly_score"] == 0.8


def test_unknown_tool_returns_error(db):
    result = execute_tool(db, "does_not_exist", {})
    assert "error" in result


def test_get_correlation_insights_filters_to_significant_and_never_claims_causation(db):
    mock_response = {
        "target": "churn",
        "disclaimer": "Korelasyon nedensellik değildir. Bu sonuçlar yalnızca istatistiksel ilişkiyi gösterir.",
        "results": [
            {
                "feature": "category_diversity",
                "correlation": 0.17,
                "p_value": 0.004,
                "mutual_information": 0.016,
                "p_value_corrected": 0.033,
                "significant": True,
            },
            {
                "feature": "trend_ratio",
                "correlation": -0.03,
                "p_value": 0.54,
                "mutual_information": 0.017,
                "p_value_corrected": 0.63,
                "significant": False,
            },
        ],
    }
    with respx.mock(assert_all_called=True) as mock:
        mock.get(url__regex=r".*/analytics/feature-importance/churn.*").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        result = execute_tool(db, "get_correlation_insights", {"target": "churn"})

    assert result["target"] == "churn"
    assert "nedensellik değildir" in result["disclaimer"]
    assert len(result["significant_relationships"]) == 1
    assert result["significant_relationships"][0]["feature"] == "category_diversity"
    assert result["significant_relationships"][0]["direction"] == "pozitif"
