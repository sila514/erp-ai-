"""
Tüm modeller burada import edilir ki Alembic ve Base.metadata.create_all
hepsini tanısın.
"""
from app.models.user import User  # noqa
from app.models.product import Product, StockMovement  # noqa
from app.models.customer import Customer  # noqa
from app.models.sale import Sale, SaleItem  # noqa
from app.models.finance import FinanceTransaction  # noqa
from app.models.ml_insight import MLInsight  # noqa
