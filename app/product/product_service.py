"""Product service for managing products and Odoo synchronization"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.auth.schemas import User as UserSchema
from app.product.schemas import Product as ProductSchema

from app.api.models import SyncResponse
from app.services.base_service import BaseService


class ProductService(BaseService):
    """Service for product operations"""

    async def create_product(self, product_data: Dict[str, Any]) -> SyncResponse:
        """Create product in local database and sync with Odoo"""
        try:
            # First create in local database

            db_product = ProductSchema(**product_data, user_id=self.current_user.id)
            self.db.add(db_product)
            await self.db.commit()
            await self.db.refresh(db_product)

            # Then sync with Odoo
            odoo_client = await self._get_odoo_client()
            odoo_id = await odoo_client.create_product(product_data)

            # Update local record with Odoo ID
            db_product.odoo_id = odoo_id
            await self.db.commit()

            # Clear cache
            await self._cache_delete(f"products:{self.current_user.id}")

            self.logger.info(
                "Product created successfully",
                product_id=db_product.id,
                odoo_id=odoo_id,
            )

            return self._create_sync_response(
                success=True,
                message="Product created and synced with Odoo",
                odoo_id=odoo_id,
                local_id=db_product.id,
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "product creation")

    async def get_products(
        self, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[Any]:
        """Get products with optional search"""
        cache_key = f"products:{self.current_user.id}:{skip}:{limit}:{search}"

        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Query from database

        stmt = select(ProductSchema).where(
            ProductSchema.user_id == self.current_user.id
        )

        if search:
            stmt = stmt.where(
                ProductSchema.name.ilike(f"%{search}%")
                | ProductSchema.default_code.ilike(f"%{search}%")
            )

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        products = result.scalars().all()

        # Cache the result
        await self._cache_set(cache_key, products, expire=300)

        return products

    async def get_product(self, product_id: int) -> Optional[Any]:
        """Get specific product by ID"""
        cache_key = f"product:{product_id}"

        # Try to get from cache first
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Query from database

        stmt = select(ProductSchema).where(
            ProductSchema.odoo_id == product_id,
            ProductSchema.user_id == self.current_user.id,
        )
        result = await self.db.execute(stmt)
        product = result.scalar_one_or_none()

        if product:
            await self._cache_set(cache_key, product, expire=300)

        return product

    async def update_product(
        self, product_id: int, update_data: Dict[str, Any]
    ) -> SyncResponse:
        """Update product and sync with Odoo"""
        try:
            # Get product from database
            stmt = select(ProductSchema).where(
                ProductSchema.odoo_id == product_id,
                # ProductSchema.user_id == self.current_user.id,
            )
            result = await self.db.execute(stmt)
            product = result.scalar_one_or_none()
            if not product:
                return self._create_sync_response(
                    success=False,
                    message="Product not found",
                    errors=["Product not found"],
                )

            # Update local record
            for field, value in update_data.items():
                setattr(product, field, value)

            await self.db.commit()

            # Sync with Odoo if Odoo ID exists
            if product.odoo_id:
                odoo_client = await self._get_odoo_client()
                await odoo_client.update_product(product.odoo_id, update_data)

            # Clear cache
            await self._cache_delete(f"product:{product_id}")
            await self._cache_delete(f"products:{self.current_user.id}")

            self.logger.info(
                "Product updated successfully",
                product_id=product_id,
                odoo_id=product.odoo_id,
            )

            return self._create_sync_response(
                success=True,
                message="Product updated and synced with Odoo",
                odoo_id=product.odoo_id,
                local_id=product_id,
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "product update")

    async def sync_products_from_odoo(self, full:bool=False) -> SyncResponse:
        """Sync products from Odoo to local database"""
        try:
            domain = []
            if not full:
                stmt = select(func.max(ProductSchema.write_date))
                result = await self.db.execute(stmt)
                last_updated_date =  result.scalar_one_or_none()
                if last_updated_date:
                    domain = [("write_date", ">", last_updated_date)]

            odoo_client = await self._get_odoo_client()
            odoo_products = await odoo_client.search_products(domain=domain)
            synced_count = 0
            for odoo_product in odoo_products:
                # Check if product already exists
                stmt = select(ProductSchema).where(
                    ProductSchema.odoo_id == odoo_product.id
                )
                result = await self.db.execute(stmt)
                existing_product = result.scalar_one_or_none()

                if existing_product:
                    # Update existing product
                    for field, value in odoo_product.model_dump(exclude=None).items():
                        if hasattr(existing_product, field):
                            setattr(existing_product, field, value)
                else:
                    db_product = ProductSchema(**odoo_product.model_dump(exclude=None))
                    db_product.id = None
                    db_product.odoo_id = odoo_product.id
                    db_product.user_id = self.current_user.id
                    self.db.add(db_product)

                synced_count += 1

            await self.db.commit()

            # Clear cache
            await self._cache_delete(f"products:{self.current_user.id}")

            self.logger.info("Products synced from Odoo", synced_count=synced_count)

            return self._create_sync_response(
                success=True,
                message=f"Successfully synced {synced_count} products from Odoo",
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "product sync from Odoo")
