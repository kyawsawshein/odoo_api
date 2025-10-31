"""Database configuration and session management"""
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
from sqlalchemy.sql import func

# Base class for models
from .database import Base


class BaseSchema(Base):
    __abstract__ = True  # ✅ prevent table creation

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OdooBaseSchema(BaseSchema):
    __abstract__ = True  # ✅ prevent table creation

    create_date = Column(String(50), server_default=func.now())
    write_date = Column(String(50), server_default=func.now())
