"""Main FastAPI application entry point"""

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.core.database import close_db, init_db
from app import dependency
from app.core.asyncpg_connect import ConfigureAsyncpg
from app.dependency import OdooAuthRequirements, ConfigureOdoo

from app.api import router as api_router
from app.auth.api.v1 import router as auth_router
from app.auth.profile_router import router as profile_router
from app.graphql.api.router import router as graphql_router
from app.project.api.v1 import router as frontend_project_router
# from app.project.optimized_router import router as optimized_project_router
# from app.contact import router as contact_router
# from app.product import router as product_router
# from app.inventory import router as inventory_router
# from app.purchase import router as purchase_router
# from app.sale import router as sale_router
# from app.account import router as account_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="FastAPI integration for Odoo 19 with Kafka, Redis, and GraphQL",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.DEBUG else ["localhost", "127.0.0.1"],
    )

    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        # await init_db()
        # Initialize other services like Redis, Kafka connections
        pass

    @app.on_event("shutdown")
    async def shutdown_event():
        # await close_db()
        # Close other connections
        pass

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
        }

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "graphql": "/graphql",
        }

    return app


# Create application instance
app = create_app()
dependency.db = ConfigureAsyncpg(
    app,
    settings.DATABASE_URI,
    db_code=settings.POSTGRES_CODE,
    **settings.POSTGRES_CONN_OPTION
)
odoo_auth_requirements = OdooAuthRequirements(
    url=settings.ODOO_URL,
    database=settings.POSTGRES_DB,
    user=settings.ODOO_USER,
    password=settings.ODOO_PASSWORD,
)

dependency.odoo = ConfigureOdoo(
    app, odoo_auth=odoo_auth_requirements, is_write_enable=settings.ODOO_WRITE_ENABLE
)

api_prefix = "/api/v1"
# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(profile_router, prefix=api_prefix, tags=["profile"])
app.include_router(api_router, prefix=api_prefix, tags=["api"])
# app.include_router(project_router, prefix=api_prefix)
app.include_router(frontend_project_router, prefix=api_prefix)
# app.include_router(optimized_project_router, prefix=api_prefix)
# app.include_router(contact_router, prefix=api_prefix)
# app.include_router(product_router, prefix=api_prefix)
# app.include_router(inventory_router, prefix=api_prefix)
# app.include_router(purchase_router, prefix=api_prefix)
# app.include_router(sale_router, prefix=api_prefix)
# app.include_router(account_router, prefix=api_prefix)
# app.include_router(graphql_router, prefix="/graphql", tags=["graphql"])



if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=4 if not settings.DEBUG else 1,
    )
