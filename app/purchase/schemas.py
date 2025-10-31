"""Database schemas for API models"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    # Boolean,
    DateTime,
    Text,
    Numeric,
    ForeignKey,
)
from app.core.schemas import BaseSchema,  OdooBaseSchema


class PurchaseOrder(OdooBaseSchema):
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
