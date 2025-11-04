"""Configuration management for the Odoo FastAPI integration"""

# from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # FastAPI Configuration
    APP_NAME: str = "Odoo FastAPI Integration"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    APP_USER: str
    APP_PASSWORD: str

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://odoo:admin@localhost:5432/odoo_api",
        env="DATABASE_URL",
    )

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Odoo Configuration
    ODOO_URL: str = Field(default="http://localhost:8090", env="ODOO_URL")
    ODOO_DATABASE: str = Field(default="odoo", env="ODOO_DATABASE")
    ODOO_USERNAME: str = Field(default="admin", env="ODOO_USERNAME")
    ODOO_PASSWORD: str = Field(default="admin", env="ODOO_PASSWORD")

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS"
    )
    KAFKA_GROUP_ID: str = Field(default="odoo-api-group", env="KAFKA_GROUP_ID")

    # Authentication
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production", env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    @property
    def allowed_origins_list(self) -> list:
        """Convert ALLOWED_ORIGINS string to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "case_sensitive": True}


# Global settings instance
settings = Settings()
