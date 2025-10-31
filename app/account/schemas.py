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

from app.core.schemas import OdooBaseSchema


class Currency(OdooBaseSchema):
    """Currencies database model"""

    __tablename__ = "currency"

    id = Column(Integer, primary_key=True, index=True)
    odoo_id = Column(Integer, nullable=True, index=True)
    name = Column(String(50), nullable=False, index=True)
    symbol = Column(String(10), nullable=False)

class AccountingMove(OdooBaseSchema):
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
