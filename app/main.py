"""Main FastAPI application entry point"""

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app import dependency
from app.core.asyncpg_connect import ConfigureAsyncpg
from app.core.logger import logger
from app.dependency import OdooAuthRequirements, ConfigureOdoo, SessionOdooConnection


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
        # Initialize logging
        logger.info("Application starting up")
        
        # await init_db()
        # Initialize other services like Redis, Kafka connections
        pass

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutting down")
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
    settings.asyncpg_dsn,
    db_code=settings.POSTGRES_CODE,
    # **settings.POSTGRES_CONN_OPTION
)
odoo_auth_requirements = OdooAuthRequirements(
    url=settings.ODOO_URL,
    database=settings.POSTGRES_DB,
    user=settings.ODOO_USERNAME,
    password=settings.ODOO_PASSWORD,
)

dependency.odoo = ConfigureOdoo(
    app,
    odoo_auth=odoo_auth_requirements,
)

# Initialize session-based Odoo connection
dependency.session_odoo = SessionOdooConnection(odoo_auth_requirements)

api_prefix = "/api/v1"

# Import routers
from app.auth.api.v1 import router as auth_router
from app.api import router as api_router
from app.auth.api.v1 import odoo_router
from app.project.api.v1 import router as frontend_project_router
from app.logging.api.v1 import router as logging_router

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(api_router, prefix=api_prefix)
app.include_router(odoo_router, prefix=api_prefix)
app.include_router(frontend_project_router, prefix=api_prefix)
app.include_router(logging_router, prefix=api_prefix)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=4 if not settings.DEBUG else 1,
    )
