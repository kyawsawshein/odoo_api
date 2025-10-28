"""Main FastAPI application entry point"""

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import close_db, init_db
from app.api import router as api_router
from app.auth import router as auth_router
from app.graphql import router as graphql_router


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
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.DEBUG else ["localhost", "127.0.0.1"],
    )

    # Include routers
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
    app.include_router(api_router, prefix="/api/v1", tags=["api"])
    app.include_router(graphql_router, prefix="/graphql", tags=["graphql"])

    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        await init_db()
        # Initialize other services like Redis, Kafka connections

    @app.on_event("shutdown")
    async def shutdown_event():
        await close_db()
        # Close other connections

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

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=4 if not settings.DEBUG else 1,
    )
