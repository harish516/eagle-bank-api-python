"""Core configuration management using Pydantic settings."""

from typing import List, Optional
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    environment: str = "development"
    debug: bool = True
    project_name: str = "Eagle Bank API"
    version: str = "1.0.0"
    api_v1_str: str = "/v1"
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/eagle_bank"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    
    # Keycloak
    keycloak_server_url: str = "http://localhost:8080"
    keycloak_realm: str = "eagle-bank"
    keycloak_client_id: str = "eagle-bank-api"
    keycloak_client_secret: Optional[str] = None
    keycloak_admin_username: str = "admin"
    keycloak_admin_password: str = "admin"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379"
    celery_result_backend: str = "redis://localhost:6379"
    
    # Event Bus
    event_bus_url: str = "redis://localhost:6379"
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    
    # Logging
    log_level: str = "DEBUG"  # Changed to DEBUG for better debugging
    log_format: str = "json"
    log_to_file: bool = False
    log_file_path: str = "logs/eagle_bank_api.log"
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
