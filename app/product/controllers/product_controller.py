"""Frontend API router for product and task management with Odoo synchronization"""

import base64
from typing import Any, Dict, List, Optional

import asyncpg
import structlog
from fastapi import HTTPException, status

# Database dependency is now passed as parameter, not imported at module level
from app.api.models.models import SyncResponse
from app.product.models.model import Pricelist, Product
from app.product.schemas.product import PricelistSchema, ProductSchema
from app.utils.model_name import Method, ModelName

logger = structlog.get_logger()


class ProductController:
    def __init__(
        self,
        odoo_connection,
    ):
        self.odoo = odoo_connection
        self.logger = logger

    async def get_products(
        self,
        skip: int = 0,
        limit: int = 100,
        write_date: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[ProductSchema]:
        """Get product dashboard data"""
        try:
            # Get product list for dashboard
            domain = [("active", "=", True), ("default_code", "!=", "")]
            if write_date:
                domain.append(("write_date", ">", write_date))
            kwargs = {
                "fields": list(Product.model_fields.keys()),
                "offset": skip,
                "limit": limit,
                "order": "write_date asc",
            }
            if search:
                domain.extend([("name", "ilike", f"%{search}%")])
            product_list = await self.odoo.execute_kw(
                model=ModelName.PRODUCT,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )
            # Get full details for each product
            products = []
            for product_data in product_list:
                product = Product(**product_data)
                self.logger.debug("Fetched product", product=product)
                products.append(
                    ProductSchema(
                        id=product.id,
                        product_tmpl_id=product.product_tmpl_id.id,
                        name=product.name,
                        product_uom_id=product.uom_id.id,
                        product_uom_name=product.uom_id.name,
                        product_qty_available=product.qty_available,
                        categ_id=product.categ_id.id,
                        categ_name=product.categ_id.name,
                        default_code=product.default_code,
                        write_date=product.write_date,
                    )
                )
            return products
        except Exception as e:
            self.logger.error("Error : %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch product dashboard: {str(e)}",
            )

    async def get_pricelists(
        self,
        skip: int,
        limit: int,
        write_date: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[PricelistSchema]:
        try:
            domain = []
            if write_date:
                domain.append(("write_date", ">", write_date))
            if search:
                domain.extend([("name", "ilike", f"%{search}%")])
            kwargs = {
                "fields": list(Pricelist.model_fields.keys()),
                "offset": skip,
                "limit": limit,
                "order": "write_date asc",
            }
            pricelist_data = await self.odoo.execute_kw(
                model=ModelName.PRICELIST,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )

            self.logger.debug("Fetched pricelists", count=len(pricelist_data))
            pricelists = []
            for pricelist in pricelist_data:
                pricelist_obj = Pricelist(**pricelist)
                pricelists.append(
                    PricelistSchema(
                        id=pricelist_obj.id,
                        name=pricelist_obj.pricelist_id.name,
                        product_id=(
                            pricelist_obj.product_id.id
                            if pricelist_obj.product_id
                            else None
                        ),
                        product_tmpl_id=(
                            pricelist_obj.product_tmpl_id.id
                            if pricelist_obj.product_tmpl_id
                            else None
                        ),
                        fixed_price=pricelist_obj.fixed_price,
                        percent_price=pricelist_obj.percent_price,
                        price_surcharge=pricelist_obj.price_surcharge,
                        price_discount=pricelist_obj.price_discount,
                        categ_id=(
                            pricelist_obj.categ_id.id
                            if pricelist_obj.categ_id
                            else None
                        ),
                        categ_name=(
                            pricelist_obj.categ_id.name
                            if pricelist_obj.categ_id
                            else None
                        ),
                        date_start=pricelist_obj.date_start,
                        date_end=pricelist_obj.date_end,
                        write_date=pricelist_obj.write_date,
                    )
                )
            return pricelists
        except Exception as err:
            self.logger.error("Failed to fetch pricelists", error=str(err))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch pricelists: {str(err)}",
            )
