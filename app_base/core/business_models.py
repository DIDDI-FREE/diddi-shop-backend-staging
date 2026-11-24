from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app_base.core.platform_models import Base


class ShopRecord(Base):
    __tablename__ = "shops"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class ProductRecord(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    shop_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class StockOperationRecord(Base):
    __tablename__ = "stock_operations"
    operation_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(128), nullable=False)


class CartRecord(Base):
    __tablename__ = "carts"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class CheckoutRecord(Base):
    __tablename__ = "checkouts"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class OrderRecord(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    shop_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    checkout_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    fulfillment_status: Mapped[str] = mapped_column(String(64), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class ClaimRecord(Base):
    __tablename__ = "claims"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class DeliveryRecord(Base):
    __tablename__ = "delivery_projections"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class BusinessUniqueConstraints:
    """Keep the constraint names discoverable for migration tooling."""

    __table_args__ = (UniqueConstraint("customer_id", name="uq_carts_customer"),)
