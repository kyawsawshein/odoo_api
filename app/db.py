"""Database connection — supports Docker (pool) and Vercel serverless.

In Docker: connection pool is created once and reused.
On Vercel: pool is created at module level and reused across warm invocations;
          cold starts get a fresh pool backed by the DATABASE_URL env var.
"""

import ssl
from urllib.parse import parse_qs, urlparse

import asyncpg
from app.config import settings, IS_VERCEL

_pool: asyncpg.Pool | None = None

# Cloud PG providers that always require SSL
_SSL_HOSTS = {
    "neon.tech",
    "vercel",
    "vercel-storage",
    "verceldb",
    "aws",
    "amazonaws.com",
    "rds.amazonaws.com",
    "googleapis.com",
    "cloudsql",
    "azure.com",
    "digitalocean",
    "supabase",
    "supabase.co",
    "render.com",
    "fly.dev",
    "elestio.app",
}


def _needs_ssl(url: str) -> bool:
    """Guess whether this database URL requires SSL."""
    host = urlparse(url).hostname or ""
    return any(suffix in host for suffix in _SSL_HOSTS)


def _make_ssl_context() -> ssl.SSLContext:
    """Create an SSL context that does not verify the server certificate.

    This is the Python equivalent of Node.js's ``{rejectUnauthorized: false}``.
    Required for cloud providers (like Elestio) that use self-signed certs.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _parse_dsn(url: str) -> tuple[str, object]:
    """Parse DATABASE_URL -> (clean_dsn, ssl_kwarg).

    asyncpg does not read sslmode from the query string, so we extract it.
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    # Extract and remove sslmode from query
    sslmode = None
    if "sslmode" in query:
        sslmode = query["sslmode"][0]

    # Rebuild URL without query (asyncpg handles DSN better without it)
    clean_url = parsed._replace(query="").geturl()

    # Determine SSL kwarg
    if sslmode in ("require", "prefer", "verify-ca", "verify-full"):
        ssl_kwarg: object = _make_ssl_context()
    elif _needs_ssl(url):
        ssl_kwarg = _make_ssl_context()  # require SSL for known cloud providers
    else:
        ssl_kwarg = None  # no SSL

    return clean_url, ssl_kwarg


async def get_pool():
    """Return the shared connection pool (Docker / warm serverless).

    Includes automatic health-check and recovery: if the cached pool exists
    but its underlying connections are dead (e.g. after a DB restart or
    network blip), the stale pool is closed and a fresh one is created.
    """
    global _pool

    if _pool is not None:
        # ── Health-check: verify the pool is still alive ──
        try:
            async with _pool.acquire(timeout=5) as conn:
                await conn.execute("SELECT 1")
            # Pool is healthy — return it
            return _pool
        except Exception as health_err:
            print(f"[DB] Pool health-check failed ({health_err}); recreating pool...")
            try:
                await _pool.close()
            except Exception:
                pass
            _pool = None

    # ── Create fresh pool ──
    print("[DB] Initializing connection pool...", settings.pg_vector_dsn)
    dsn, ssl_kwarg = _parse_dsn(settings.pg_vector_dsn)

    max_size = 5 if IS_VERCEL else 20
    print(
        f"[DB] Creating pool → {dsn.split('@')[-1] if '@' in dsn else dsn}"
        f"  ssl={ssl_kwarg}  max={max_size}  vercel={IS_VERCEL}"
    )
    print("DB URL (masked):", dsn)
    try:
        _pool = await asyncpg.create_pool(
            dsn,
            min_size=1,
            max_size=max_size,
            ssl=ssl_kwarg,
            command_timeout=30,
        )
    except Exception as e:
        print("[DB] Error creating pool:", e)
        raise

    return _pool


async def get_connection():
    """Return a single connection directly (useful for short-lived contexts).

    On Vercel this acquires from the pool; the pool itself is cached at
    module level across warm invocations.
    """
    pool = await get_pool()
    return await pool.acquire()
