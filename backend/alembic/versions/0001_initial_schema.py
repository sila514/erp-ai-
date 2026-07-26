"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-26

Modellerin (backend/app/models/*.py) birebir karşılığı. Elle yazıldı çünkü
GUID (dialect-agnostic UUID) tipiyle autogenerate belirsiz kod üretiyor ve
şema zaten modellerden tam olarak biliniyor.
"""
from alembic import op
import sqlalchemy as sa

from app.core.types import GUID

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(128), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "MANAGER", "SALES", "INVENTORY", "FINANCE", name="userrole"),
            nullable=False,
            server_default="SALES",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("lead_time_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_category", "products", ["category"])

    op.create_table(
        "stock_movements",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("product_id", GUID(), nullable=False),
        sa.Column("movement_type", sa.String(16), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"])
    op.create_index("ix_stock_movements_created_at", "stock_movements", ["created_at"])

    op.create_table(
        "customers",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(128), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("segment", sa.String(64), nullable=True),
        sa.Column("churn_risk_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("lifetime_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_segment", "customers", ["segment"])

    op.create_table(
        "sales",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("customer_id", GUID(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "COMPLETED", "CANCELLED", name="salestatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("is_flagged_anomaly", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("anomaly_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sales_customer_id", "sales", ["customer_id"])
    op.create_index("ix_sales_created_at", "sales", ["created_at"])

    op.create_table(
        "sale_items",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("sale_id", GUID(), sa.ForeignKey("sales.id"), nullable=False),
        sa.Column("product_id", GUID(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
    )
    op.create_index("ix_sale_items_sale_id", "sale_items", ["sale_id"])
    op.create_index("ix_sale_items_product_id", "sale_items", ["product_id"])

    op.create_table(
        "finance_transactions",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "type",
            sa.Enum("INCOME", "EXPENSE", name="transactiontype"),
            nullable=False,
        ),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_finance_transactions_category", "finance_transactions", ["category"])
    op.create_index("ix_finance_transactions_created_at", "finance_transactions", ["created_at"])

    op.create_table(
        "ml_insights",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("insight_type", sa.String(64), nullable=False),
        sa.Column("entity_id", GUID(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ml_insights_insight_type", "ml_insights", ["insight_type"])
    op.create_index("ix_ml_insights_entity_id", "ml_insights", ["entity_id"])
    op.create_index("ix_ml_insights_generated_at", "ml_insights", ["generated_at"])


def downgrade() -> None:
    op.drop_table("ml_insights")
    op.drop_table("finance_transactions")
    op.drop_table("sale_items")
    op.drop_table("sales")
    op.drop_table("customers")
    op.drop_table("stock_movements")
    op.drop_table("products")
    op.drop_table("users")

    bind = op.get_bind()
    sa.Enum(name="salestatus").drop(bind, checkfirst=True)
    sa.Enum(name="transactiontype").drop(bind, checkfirst=True)
    sa.Enum(name="userrole").drop(bind, checkfirst=True)
