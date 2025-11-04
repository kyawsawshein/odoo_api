from typing import Tuple, Iterable
import asyncpg

def build_query(query: str) -> str:
    return query%tuple(f"${a}" for a in range(1,query.count("%s")+1))

async def prepare_and_fetch(conn: asyncpg.Connection, query: str, *args):
    stmt = await conn.prepare(query)
    return await stmt.fetch(*args)

async def prepare_and_fetchrow(conn: asyncpg.Connection, query: str, *args):
    stmt = await conn.prepare(query)
    return await stmt.fetchrow(*args)
