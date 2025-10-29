"""Main API router for Odoo FastAPI integration"""

from typing import List, Optional

import structlog
from app.api.models import (
    AccountingMove,
    AccountingMoveCreate,
    BulkSyncRequest,
    BulkSyncResponse,
    Contact,
    ContactCreate,
    ContactUpdate,
    Delivery,
    DeliveryCreate,
    Inventory,
    InventoryCreate,
    InventoryUpdate,
    Product,
    ProductCreate,
    ProductUpdate,
    PurchaseOrder,
    PurchaseOrderCreate,
    SaleOrder,
    SaleOrderCreate,
    SyncResponse,
)
from app.auth.router import get_current_user
from app.auth.schemas import User as UserSchema

# from app.services.delivery_service import DeliveryService
# from app.services.accounting_service import AccountingService
# from app.kafka.producer import KafkaProducer
from app.cache.redis_client import redis_client
from app.database import get_db
from app.services.contact_service import ContactService
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService
from app.services.purchase_service import PurchaseService
from app.services.sale_service import SaleService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter()


# Contact Endpoints
@router.post("/contacts", response_model=SyncResponse, tags=["contacts"])
async def create_contact(
    contact: ContactCreate,
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new contact and sync with Odoo"""
    service = ContactService(db, current_user)

    try:
        result = await service.create_contact(contact.dict())

        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-contacts",
        #     {
        #         "action": "create",
        #         "user_id": current_user.id,
        #         "contact_data": contact.dict(),
        #         "local_id": result.local_id
        #     }
        # )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contact: {str(e)}",
        )


@router.get("/contacts", response_model=List[Contact], tags=["contacts"])
async def get_contacts(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get contacts with pagination and search"""
    service = ContactService(db, current_user)
    return await service.get_contacts(skip=skip, limit=limit, search=search)


@router.get("/contacts/{contact_id}", response_model=Contact, tags=["contacts"])
async def get_contact(
    contact_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific contact by ID"""
    service = ContactService(db, current_user)
    print("contact service :", service)
    contact = await service.get_contact(contact_id)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )

    return contact


@router.put("/contacts/{contact_id}", response_model=SyncResponse, tags=["contacts"])
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update contact and sync with Odoo"""
    service = ContactService(db, current_user)

    try:
        result = await service.update_contact(
            contact_id, contact.dict(exclude_unset=True)
        )

        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-contacts",
        #     {
        #         "action": "update",
        #         "user_id": current_user.id,
        #         "contact_id": contact_id,
        #         "update_data": contact.dict(exclude_unset=True)
        #     }
        # )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact: {str(e)}",
        )


@router.post("/contacts/sync", response_model=SyncResponse, tags=["contacts"])
async def sync_contacts(
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync Contact data with Odoo"""
    service = ContactService(db, current_user)
    try:
        result = await service.sync_contacts_from_odoo()

        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-contact",
        #     {
        #         "action": "sync",
        #         "user_id": current_user.id
        #     }
        # )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Contacts: {str(e)}",
        )


# Product Endpoints
@router.post("/products", response_model=SyncResponse, tags=["products"])
async def create_product(
    product: ProductCreate,
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new product and sync with Odoo"""
    service = ProductService(db, current_user)

    try:
        result = await service.create_product(product.dict())

        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-products",
        #     {
        #         "action": "create",
        #         "user_id": current_user.id,
        #         "product_data": product.dict(),
        #         "local_id": result.local_id
        #     }
        # )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}",
        )


@router.get("/products", response_model=List[Product], tags=["products"])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get products with pagination and search"""
    service = ProductService(db, current_user)
    return await service.get_products(skip=skip, limit=limit, search=search)


@router.get("/products/{product_id}", response_model=Product, tags=["products"])
async def get_product(
    product_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific product by ID"""
    service = ProductService(db, current_user)
    product = await service.get_product(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    return product


@router.put("/products/{product_id}", response_model=SyncResponse, tags=["products"])
async def update_product(
    product_id: int,
    product: ProductUpdate,
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update product and sync with Odoo"""
    service = ProductService(db, current_user)

    try:
        result = await service.update_product(
            product_id, product.dict(exclude_unset=True)
        )

        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-products",
        #     {
        #         "action": "update",
        #         "user_id": current_user.id,
        #         "product_id": product_id,
        #         "update_data": product.dict(exclude_unset=True)
        #     }
        # )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}",
        )


@router.post("/product/sync", response_model=SyncResponse, tags=["products"])
async def sync_porducts(
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync Contact data with Odoo"""
    service = ProductService(db, current_user)
    try:
        result = await service.sync_products_from_odoo()

        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-contact",
        #     {
        #         "action": "sync",
        #         "user_id": current_user.id
        #     }
        # )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Products: {str(e)}",
        )


# Inventory Endpoints
@router.get("/inventory", response_model=List[Inventory], tags=["inventory"])
async def get_inventory(
    product_id: Optional[int] = None,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get inventory data"""
    service = InventoryService(db, current_user)
    return await service.get_inventory(product_id=product_id)


@router.post("/inventory/sync", response_model=SyncResponse, tags=["inventory"])
async def sync_inventory(
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync inventory data with Odoo"""
    service = InventoryService(db, current_user)

    try:
        result = await service.sync_inventory()

        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-inventory",
        #     {
        #         "action": "sync",
        #         "user_id": current_user.id
        #     }
        # )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync inventory: {str(e)}",
        )


# Purchase Order Endpoints
@router.post("/purchase-orders", response_model=SyncResponse, tags=["purchase"])
async def create_purchase_order(
    order: PurchaseOrderCreate,
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new purchase order and sync with Odoo"""
    service = PurchaseService(db, current_user)

    try:
        result = await service.create_purchase_order(order.dict())

        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-purchase",
        #     {
        #         "action": "create",
        #         "user_id": current_user.id,
        #         "order_data": order.dict(),
        #         "local_id": result.local_id
        #     }
        # )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create purchase order: {str(e)}",
        )


@router.get("/purchase-orders", response_model=List[PurchaseOrder], tags=["purchase"])
async def get_purchase_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get purchase orders"""
    service = PurchaseService(db, current_user)
    return await service.get_purchase_orders(skip=skip, limit=limit)


# Sale Order Endpoints
@router.post("/sale-orders", response_model=SyncResponse, tags=["sales"])
async def create_sale_order(
    order: SaleOrderCreate,
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new sale order and sync with Odoo"""
    service = SaleService(db, current_user)

    try:
        result = await service.create_sale_order(order.dict())

        # Send to Kafka for async processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-sales",
        #     {
        #         "action": "create",
        #         "user_id": current_user.id,
        #         "order_data": order.dict(),
        #         "local_id": result.local_id
        #     }
        # )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sale order: {str(e)}",
        )


@router.get("/sale-orders", response_model=List[SaleOrder], tags=["sales"])
async def get_sale_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get sale orders"""
    service = SaleService(db, current_user)
    return await service.get_sale_orders(skip=skip, limit=limit)


# Bulk Operations
@router.post("/bulk-sync", response_model=BulkSyncResponse, tags=["bulk"])
async def bulk_sync(
    request: BulkSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bulk sync multiple entities with Odoo"""
    try:
        # Send to Kafka for async bulk processing
        # background_tasks.add_task(
        #     # KafkaProducer.send_message,
        #     "odoo-bulk-sync",
        #     {
        #         "user_id": current_user.id,
        #         "data": request.dict()
        #     }
        # )

        return BulkSyncResponse(
            success=True,
            message="Bulk sync request queued for processing",
            results={},
            total_processed=0,
            total_success=0,
            total_failed=0,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue bulk sync: {str(e)}",
        )


# Cache Management
@router.delete("/cache", tags=["cache"])
async def clear_cache(current_user: UserSchema = Depends(get_current_user)):
    """Clear application cache"""
    try:
        await redis_client.flush_all()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )
