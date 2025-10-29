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
from sqlalchemy.sql import func
from app.database import Base


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
    create_date = Column(String(50), nullable=False)
    write_date = Column(String(50), nullable=False)
