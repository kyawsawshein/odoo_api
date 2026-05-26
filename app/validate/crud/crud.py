"""
CRUD operations for product_info and product_category tables.

The core invariant: only records with a ``last_record`` timestamp
strictly greater than the current MAX(last_record) in the target table
are inserted or updated.  This ensures a differential (forward-only)
sync from the ERP, preventing stale data from overwriting fresh data.
"""

from datetime import datetime
from typing import Optional

import asyncpg

from app.validate.models.model import ProductCategorySyncItem, ProductInfoSyncItem

# ── Sentinel ───────────────────────────────────────────────────────────

EPOCH = "1970-01-01 00:00:00"
"""Fallback sentinel used when a table has no rows."""


# ── Max last_record ────────────────────────────────────────────────────


async def get_max_last_record(
    conn: asyncpg.Connection,
    table: str,
) -> Optional[str]:
    """Return the maximum ``last_record`` value in *table*, or ``None``.

    ``table`` must be one of ``'product_info'`` or ``'product_category'``
    (caller is responsible for validating; we trust the caller).
    """
    datetime_format = "%Y-%m-%d %H:%M:%S"
    row = await conn.fetchrow(f'SELECT MAX("last_record") AS mx FROM {table}')
    if row:
        return row["mx"].strftime(datetime_format)
    return None


# ── product_info upsert ────────────────────────────────────────────────


async def upsert_product_info_batch(
    conn: asyncpg.Connection,
    records: list[ProductInfoSyncItem],
) -> tuple[int, int]:
    """Upsert a batch of records into ``product_info``.

    Returns ``(inserted_count, updated_count)``.
    """
    if not records:
        return 0, 0

    # Pre-fetch existing SKUs to distinguish inserts from updates
    # skus = [r.sku for r in records]
    # existing_rows = await conn.fetch(
    #     "SELECT sku FROM product_info WHERE sku = ANY($1)", skus
    # )
    # existing_skus: set[str] = {row["sku"] for row in existing_rows}

    inserted = 0
    updated = 0

    for rec in records:
        await conn.execute(
            """
            INSERT INTO product_info (
                sku,
                barcode,
                product,
                category,
                customer,
                price,
                last_record
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (sku)
            DO UPDATE SET
                barcode     = EXCLUDED.barcode,
                product     = EXCLUDED.product,
                category    = EXCLUDED.category,
                customer    = EXCLUDED.customer,
                price       = EXCLUDED.price,
                last_record = EXCLUDED.last_record
            """,
            rec.sku,
            rec.barcode or None,
            rec.product or "",
            rec.category or "",
            rec.customer or "",
            rec.price,
            rec.last_record,
        )
        # if rec.sku in existing_skus:
        #     updated += 1
        # else:
        inserted += 1

    return inserted, updated


# ── product_category insert ────────────────────────────────────────────


async def insert_product_category_batch(
    conn: asyncpg.Connection,
    records: list[ProductCategorySyncItem],
) -> int:
    """Insert a batch of records into ``product_category`` (no upsert).

    Returns the number of rows inserted.
    """
    if not records:
        return 0

    inserted = 0
    for rec in records:
        await conn.execute(
            """
            INSERT INTO product_category (
                product,
                category,
                customer,
                price,
                last_record
            )
            VALUES ($1, $2, $3, $4, $5)
            """,
            rec.product or "",
            rec.category or "",
            rec.customer or "",
            rec.price,
            rec.last_record,
        )
        inserted += 1

    return inserted
