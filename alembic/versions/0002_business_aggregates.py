"""business aggregate persistence"""
import sqlalchemy as sa

from alembic import op

revision = "0002_business_aggregates"
down_revision = "0001_platform_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shops",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("owner_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_index("ix_shops_owner_id", "shops", ["owner_id"])
    op.create_table(
        "products",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("shop_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_index("ix_products_shop_id", "products", ["shop_id"])
    op.create_table(
        "stock_operations",
        sa.Column("operation_id", sa.String(255), primary_key=True),
        sa.Column("product_id", sa.String(128), nullable=False),
    )
    op.create_table(
        "carts",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("customer_id", sa.String(128), nullable=False, unique=True),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_table(
        "checkouts",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("customer_id", sa.String(128), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_index("ix_checkouts_customer_id", "checkouts", ["customer_id"])
    op.create_table(
        "orders",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("shop_id", sa.String(128), nullable=False),
        sa.Column("checkout_id", sa.String(128), nullable=False),
        sa.Column("fulfillment_status", sa.String(64), nullable=False),
        sa.Column("payment_status", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_index("ix_orders_shop_id", "orders", ["shop_id"])
    op.create_index("ix_orders_checkout_id", "orders", ["checkout_id"])
    op.create_table(
        "claims",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("order_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
    )
    op.create_index("ix_claims_order_id", "claims", ["order_id"])
    op.create_table(
        "delivery_projections",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("order_id", sa.String(128), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("delivery_projections")
    op.drop_index("ix_claims_order_id", table_name="claims")
    op.drop_table("claims")
    op.drop_index("ix_orders_checkout_id", table_name="orders")
    op.drop_index("ix_orders_shop_id", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_checkouts_customer_id", table_name="checkouts")
    op.drop_table("checkouts")
    op.drop_table("carts")
    op.drop_table("stock_operations")
    op.drop_index("ix_products_shop_id", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_shops_owner_id", table_name="shops")
    op.drop_table("shops")
