"""
Controllers for the validate module.
"""

from datetime import datetime
from typing import Optional

import structlog

from app.db import get_pool
from app.product.controllers.product_controller import ProductController
from app.product.schemas.product import PricelistSchema, ProductSchema
from app.validate.crud.crud import (
    get_max_last_record,
    insert_product_category_batch,
    upsert_product_info_batch,
)
from app.validate.models.model import (
    ProductCategorySyncItem,
    ProductInfoSyncItem,
    SyncProductsRequest,
    SyncProductsResponse,
)

logger = structlog.get_logger()


# ── Helpers ────────────────────────────────────────────────────────────


def _parse_write_date(raw: Optional[str]) -> Optional[datetime]:
    """Parse an Odoo ``write_date`` string into a datetime, or ``None``."""
    if not raw:
        return None
    try:
        # Odoo returns "YYYY-MM-DD HH:MM:SS" (no T separator)
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            logger.warning("sync_products.unparseable_date", raw=raw)
            return None


def _products_to_sync_items(
    products: list[ProductSchema], customer: str = ""
) -> list[ProductInfoSyncItem]:
    """Transform Odoo product records into ``ProductInfoSyncItem``."""
    return [
        ProductInfoSyncItem(
            sku=p.default_code or "",
            barcode=p.barcode or "",
            product=p.name or "",
            category=getattr(p, "categ_name", "") or "",
            customer=customer,
            price=p.list_price,
            last_record=_parse_write_date(p.write_date),
        )
        for p in products
    ]


def _pricelists_to_sync_items(
    pricelists: list[PricelistSchema], customer: str = ""
) -> list[ProductCategorySyncItem]:
    """Transform Odoo pricelist records into ``ProductCategorySyncItem``."""
    return [
        ProductCategorySyncItem(
            product=getattr(pl, "default_code", "") or "",
            category=pl.categ_name or "",
            customer=customer,
            price=pl.fixed_price,
            last_record=_parse_write_date(pl.write_date),
        )
        for pl in pricelists
    ]


# ── Main controller ────────────────────────────────────────────────────


class ValidateController:
    def __init__(
        self,
        odoo_connection,
    ):
        self.odoo = odoo_connection
        self.logger = logger

    async def sync_products(
        self,
        body: SyncProductsRequest,
        customer: str = "zervi",
        limit: int = 100,
        write_date: Optional[str] = None,
    ) -> SyncProductsResponse:
        """Orchestrate the differential sync of product_info and product_category.

        Data sources (in priority order):
          1. Explicit records in *body* (if provided).
          2. Auto-fetched from Odoo ``product.product`` and
             ``product.pricelist.item`` via the session Odoo connection.

        Only records whose ``last_record`` is strictly greater than the
        current ``MAX(last_record)`` in each table are persisted.  Records
        with ``last_record = None`` are always considered newer.
        """
        self.logger.info(
            "sync_products.start",
            customer=customer,
            limit=limit,
            write_date=write_date,
        )

        # ── Acquire database pool ──
        try:
            pool = await get_pool()
        except Exception as exc:
            self.logger.error("sync_products.db_pool_failed", error=str(exc))
            return SyncProductsResponse(
                detail=f"Database unavailable: {exc}",
            )

        try:
            async with pool.acquire() as conn:
                # ── Resolve data source ──
                has_explicit_pi = bool(body.product_info)
                has_explicit_pc = bool(body.product_category)

                pi_items: list[ProductInfoSyncItem] = list(body.product_info)
                pc_items: list[ProductCategorySyncItem] = list(body.product_category)

                # ── Snapshot current max timestamps ──
                pi_max_before = await get_max_last_record(conn, "product_info")
                pc_max_before = await get_max_last_record(conn, "product_category")

                self.logger.info(
                    "sync_products.snapshot",
                    customer=customer,
                    limit=limit,
                    write_date=write_date,
                    pi_max_before=str(pi_max_before),
                    pc_max_before=str(pc_max_before),
                    pi_incoming=len(pi_items),
                    pc_incoming=len(pc_items),
                )

                # ── Auto-fetch from Odoo when body is empty ──
                if not has_explicit_pi or not has_explicit_pc:
                    ctrl = ProductController(self.odoo)
                    self.logger.info("sync_products.fetching_from_odoo")

                    try:
                        if not has_explicit_pi:
                            odoo_products: list[ProductSchema] = await ctrl.get_products(
                                skip=0,
                                limit=limit,
                                write_date=pi_max_before,
                            )
                            pi_items = _products_to_sync_items(odoo_products, customer)
                            self.logger.info(
                                "sync_products.odoo_products_fetched",
                                count=len(pi_items),
                            )

                        if not has_explicit_pc:
                            odoo_pricelists: list[PricelistSchema] = (
                                await ctrl.get_pricelists(
                                    skip=0,
                                    limit=limit,
                                    write_date=pc_max_before,
                                )
                            )
                            pc_items = _pricelists_to_sync_items(
                                odoo_pricelists, customer
                            )
                            self.logger.info(
                                "sync_products.odoo_pricelists_fetched",
                                count=len(pc_items),
                            )
                    except Exception as odoo_exc:
                        self.logger.error(
                            "sync_products.odoo_fetch_failed",
                            error=str(odoo_exc),
                        )
                        return SyncProductsResponse(
                            detail=f"Odoo fetch failed: {odoo_exc}",
                            product_info_max_before=pi_max_before,
                            product_category_max_before=pc_max_before,
                        )

                self.logger.info(
                    "sync_products.filtered",
                    pi_incoming=len(pi_items),
                    pc_incoming=len(pc_items),
                )

                # ── Persist inside a transaction ──
                inserted_pi = 0
                updated_pi = 0
                inserted_pc = 0

                async with conn.transaction():
                    if pi_items:
                        inserted_pi, updated_pi = await upsert_product_info_batch(
                            conn, pi_items
                        )
                    if pc_items:
                        inserted_pc = await insert_product_category_batch(
                            conn, pc_items
                        )

                detail = (
                    f"product_info: {inserted_pi} inserted, {updated_pi} updated; "
                    f"product_category: {inserted_pc} inserted"
                )
                self.logger.info("sync_products.done", detail=detail)

                return SyncProductsResponse(
                    product_info_inserted=inserted_pi,
                    product_info_updated=updated_pi,
                    product_category_inserted=inserted_pc,
                    product_info_max_before=pi_max_before,
                    product_category_max_before=pc_max_before,
                    detail=detail,
                )

        except Exception as exc:
            self.logger.error("sync_products.unexpected_error", error=str(exc))
            return SyncProductsResponse(
                detail=f"Unexpected error: {exc}",
            )
