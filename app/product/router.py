"""Main API router for Odoo FastAPI integration"""

from typing import List, Optional

import structlog
from app.api.models import SyncResponse
from app.auth.router import get_current_user
from app.auth.schemas import User as UserSchema
from app.database import get_db
from app.product.models.model import Product, ProductCreate, ProductUpdate
from app.product.product_service import ProductService

# from app.kafka.producer import KafkaProducer
from app.product.route_name import Router
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/products", tags=["Products"])


# Product Endpoints
@router.post(Router.product, response_model=SyncResponse)
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
        #     KafkaProducer.send_message,
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


@router.get(Router.product, response_model=List[Product])
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


@router.get(Router.product_id, response_model=Product)
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


@router.put(Router.product_id, response_model=SyncResponse)
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


@router.post(Router.product_sync, response_model=SyncResponse)
async def sync_porducts(
    background_tasks: BackgroundTasks,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    full: bool = False,
):
    """Sync Contact data with Odoo"""
    service = ProductService(db, current_user)
    try:
        result = await service.sync_products_from_odoo(full)

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
