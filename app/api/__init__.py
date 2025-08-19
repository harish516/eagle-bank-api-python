"""API module initialization."""

from .dependencies import get_database, get_db, get_redis
from .middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    CircuitBreakerMiddleware,
    MetricsMiddleware,
)

__all__ = [
    "get_database",
    "get_db",
    "get_redis",
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware",
    "RateLimitMiddleware",
    "CircuitBreakerMiddleware",
    "MetricsMiddleware",
]
