"""Configuration management for the Odoo FastAPI integration"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # FastAPI Configuration
    APP_NAME: str = "Odoo FastAPI Integration"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Authentication
    API_KEY: str = Field(
        default="your-secret-key-here-change-in-production", env="SECRET_KEY"
    )
    API_KEY_NAME: str
    COOKIE_DOMAIN: str
    API_USER: str
    API_PASSWORD: str

    API_JWT_ISSUER: str
    API_JWT_AUDIENCES: str
    API_JWT_ALGORITHM: str
    API_JWT_TOKEN_DURATION: int

    # Database Configuration
    DATABASE_URL: str = Field(
        default="",
        env="DATABASE_URL",
    )

    POSTGRES_CODE: Optional[str] = "rw_odoo_db"
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str
    POSTGRES_CONN_OPTION: dict
    DATABASE_URI: Optional[str] = None

    @property
    def asyncpg_dsn(self) -> str:
        """Generate asyncpg DSN from PostgreSQL settings"""
        if self.DATABASE_URI:
            return self.DATABASE_URI
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Odoo Configuration
    ODOO_URL: str = Field(default="http://localhost:8090", env="ODOO_URL")
    ODOO_DATABASE: str = Field(default="odoo", env="ODOO_DATABASE")
    ODOO_USERNAME: str = Field(default="admin", env="ODOO_USERNAME")
    ODOO_PASSWORD: str = Field(default="admin", env="ODOO_PASSWORD")
    # ODOO_WRITE_ENABLE: bool = False
    # ODOO_API_HEADER: str
    ODOO_API_KEY: str

    ODOO_JWT_AUTHZ_HOST: str
    ODOO_JWT_AUTHZ_LOGIN_EP: str
    ODOO_JWT_AUTHZ_CALL_EP: str
    ODOO_JWT_AUTHZ_TIMEOUT: int

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_GROUP_ID: str = Field(default="odoo-api-group", env="KAFKA_GROUP_ID")

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
