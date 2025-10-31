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
from app.core.schemas import BaseSchema, OdooBaseSchema


class Product(OdooBaseSchema):
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
