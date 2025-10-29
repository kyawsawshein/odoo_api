"""Database schemas for API models"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    Numeric,
    ForeignKey,
)
from sqlalchemy.sql import func
from app.database import Base


class Contact(Base):
    """Contact database model"""

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    odoo_id = Column(Integer, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(255), nullable=True)
    street = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    country_id = Column(Integer, nullable=True)
    is_company = Column(Boolean, default=False)
    company_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Product(Base):
    """Product database model"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    odoo_id = Column(Integer, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    default_code = Column(String(255), nullable=True)
    list_price = Column(Numeric(15, 2), nullable=True)
    standard_price = Column(Numeric(15, 2), nullable=True)
    type = Column(String(50), default="product")
    categ_id = Column(Integer, nullable=True)
    uom_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Inventory(Base):
    """Inventory database model"""

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    odoo_id = Column(Integer, nullable=True, index=True)
    product_id = Column(Integer, nullable=False)
    location_id = Column(Integer, nullable=True)
    quantity = Column(Numeric(15, 2), nullable=False)
    lot_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PurchaseOrder(Base):
    """Purchase order database model"""

    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    odoo_id = Column(Integer, nullable=True, index=True)
    partner_id = Column(Integer, nullable=False)
    date_order = Column(DateTime(timezone=True), nullable=False)
    state = Column(String(50), default="draft")
    amount_total = Column(Numeric(15, 2), nullable=True)
    order_line = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SaleOrder(Base):
    """Sale order database model"""

    __tablename__ = "sale_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    odoo_id = Column(Integer, nullable=True, index=True)
    partner_id = Column(Integer, nullable=False)
    date_order = Column(DateTime(timezone=True), nullable=False)
    state = Column(String(50), default="draft")
    amount_total = Column(Numeric(15, 2), nullable=True)
    order_line = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Delivery(Base):
    """Delivery database model"""

    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    odoo_id = Column(Integer, nullable=True, index=True)
    partner_id = Column(Integer, nullable=False)
    picking_type_id = Column(Integer, nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    state = Column(String(50), default="draft")
    move_lines = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AccountingMove(Base):
    """Accounting move database model"""

    __tablename__ = "accounting_moves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    odoo_id = Column(Integer, nullable=True, index=True)
    journal_id = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    ref = Column(String(255), nullable=True)
    state = Column(String(50), default="draft")
    amount_total = Column(Numeric(15, 2), nullable=True)
    line_ids = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
