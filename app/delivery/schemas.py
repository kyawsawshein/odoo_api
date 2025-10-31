"""Database schemas for API models"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    # Boolean,
    DateTime,
    Text,
    # Numeric,
    ForeignKey,
)
from app.core.schemas import BaseSchema, OdooBaseSchema


class Delivery(OdooBaseSchema):
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
