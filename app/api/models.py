"""Pydantic models for API requests and responses"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal


class ContactBase(BaseModel):
    """Base contact model"""
    name: str = Field(..., description="Contact name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    country_id: Optional[int] = Field(None, description="Country ID")
    is_company: bool = Field(False, description="Is company")
    company_type: Optional[str] = Field(None, description="Company type")


class ContactCreate(ContactBase):
    """Contact creation model"""
    pass


class ContactUpdate(BaseModel):
    """Contact update model"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country_id: Optional[int] = None


class Contact(ContactBase):
    """Contact response model"""
    id: int
    odoo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Base product model"""
    name: str = Field(..., description="Product name")
    default_code: Optional[str] = Field(None, description="Internal reference")
    list_price: Optional[Decimal] = Field(None, description="Sales price")
    standard_price: Optional[Decimal] = Field(None, description="Cost price")
    type: str = Field("product", description="Product type (product/consu/service)")
    categ_id: Optional[int] = Field(None, description="Category ID")
    uom_id: Optional[int] = Field(None, description="Unit of measure ID")
    description: Optional[str] = Field(None, description="Product description")


class ProductCreate(ProductBase):
    """Product creation model"""
    pass


class ProductUpdate(BaseModel):
    """Product update model"""
    name: Optional[str] = None
    default_code: Optional[str] = None
    list_price: Optional[Decimal] = None
    standard_price: Optional[Decimal] = None
    description: Optional[str] = None


class Product(ProductBase):
    """Product response model"""
    id: int
    odoo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryBase(BaseModel):
    """Base inventory model"""
    product_id: int = Field(..., description="Product ID")
    location_id: int = Field(..., description="Location ID")
    quantity: Decimal = Field(..., description="Quantity")
    lot_id: Optional[int] = Field(None, description="Lot/Serial number ID")


class InventoryCreate(InventoryBase):
    """Inventory creation model"""
    pass


class InventoryUpdate(BaseModel):
    """Inventory update model"""
    quantity: Optional[Decimal] = None
    location_id: Optional[int] = None


class Inventory(InventoryBase):
    """Inventory response model"""
    id: int
    odoo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    """Base purchase order model"""
    partner_id: int = Field(..., description="Supplier ID")
    date_order: datetime = Field(..., description="Order date")
    order_line: List[Dict] = Field(default_factory=list, description="Order lines")


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation model"""
    pass


class PurchaseOrder(PurchaseOrderBase):
    """Purchase order response model"""
    id: int
    odoo_id: Optional[int] = None
    state: str
    amount_total: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SaleOrderBase(BaseModel):
    """Base sale order model"""
    partner_id: int = Field(..., description="Customer ID")
    date_order: datetime = Field(..., description="Order date")
    order_line: List[Dict] = Field(default_factory=list, description="Order lines")


class SaleOrderCreate(SaleOrderBase):
    """Sale order creation model"""
    pass


class SaleOrder(SaleOrderBase):
    """Sale order response model"""
    id: int
    odoo_id: Optional[int] = None
    state: str
    amount_total: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeliveryBase(BaseModel):
    """Base delivery model"""
    partner_id: int = Field(..., description="Partner ID")
    picking_type_id: int = Field(..., description="Picking type ID")
    scheduled_date: datetime = Field(..., description="Scheduled date")
    move_lines: List[Dict] = Field(default_factory=list, description="Move lines")


class DeliveryCreate(DeliveryBase):
    """Delivery creation model"""
    pass


class Delivery(DeliveryBase):
    """Delivery response model"""
    id: int
    odoo_id: Optional[int] = None
    state: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccountingMoveBase(BaseModel):
    """Base accounting move model"""
    journal_id: int = Field(..., description="Journal ID")
    # date: date = Field(..., description="Move date")
    ref: Optional[str] = Field(None, description="Reference")
    line_ids: List[Dict] = Field(default_factory=list, description="Move lines")


class AccountingMoveCreate(AccountingMoveBase):
    """Accounting move creation model"""
    pass


class AccountingMove(AccountingMoveBase):
    """Accounting move response model"""
    id: int
    odoo_id: Optional[int] = None
    state: str
    amount_total: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SyncResponse(BaseModel):
    """Synchronization response model"""
    success: bool
    message: str
    odoo_id: Optional[int] = None
    local_id: Optional[int] = None
    errors: List[str] = Field(default_factory=list)


class BulkSyncRequest(BaseModel):
    """Bulk synchronization request model"""
    contacts: List[ContactCreate] = Field(default_factory=list)
    products: List[ProductCreate] = Field(default_factory=list)
    inventory: List[InventoryCreate] = Field(default_factory=list)
    purchase_orders: List[PurchaseOrderCreate] = Field(default_factory=list)
    sale_orders: List[SaleOrderCreate] = Field(default_factory=list)
    deliveries: List[DeliveryCreate] = Field(default_factory=list)
    accounting_moves: List[AccountingMoveCreate] = Field(default_factory=list)


class BulkSyncResponse(BaseModel):
    """Bulk synchronization response model"""
    success: bool
    message: str
    results: Dict[str, List[SyncResponse]]
    total_processed: int
    total_success: int
    total_failed: int