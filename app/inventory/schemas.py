"""Database schemas for API models"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    # Boolean,
    DateTime,
    # Text,
    Numeric,
    ForeignKey,
)
from app.core.schemas import OdooBaseSchema


class UomSchema(OdooBaseSchema):
    """Inventory database model"""

    __tablename__ = "uom"

    id = Column(Integer, primary_key=True, index=True)
    odoo_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)


class CategorySchema(OdooBaseSchema):
    """Inventory database model"""

    __tablename__ = "category"

    id = Column(Integer, primary_key=True, index=True)
    odoo_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)


class Inventory(OdooBaseSchema):
    """Inventory database model"""

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    odoo_id = Column(Integer, nullable=True, index=True)
    product_id = Column(Integer, nullable=False)
    location_id = Column(Integer, nullable=True)
    quantity = Column(Numeric(15, 2), nullable=False)
    lot_id = Column(Integer, nullable=True)
