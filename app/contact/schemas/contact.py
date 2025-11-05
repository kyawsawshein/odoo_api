"""Database schemas for API models"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    # Text,
    # Numeric,
    ForeignKey,
)
from sqlalchemy.sql import func
# from app.core.schemas import BaseSchema, OdooBaseSchema


# class Contact(OdooBaseSchema):
#     """Contact database model"""

#     __tablename__ = "contacts"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     odoo_id = Column(Integer, nullable=True, index=True)
#     name = Column(String(255), nullable=False)
#     email = Column(String(255), nullable=True)
#     phone = Column(String(255), nullable=True)
#     street = Column(String(255), nullable=True)
#     city = Column(String(100), nullable=True)
#     country_id = Column(Integer, nullable=True)
#     is_company = Column(Boolean, default=False)
#     company_type = Column(String(50), nullable=True)
