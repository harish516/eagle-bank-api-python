"""Main FastAPI application entry point."""

import logging

from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core import create_app, settings
from app.api.v1 import accounts, transactions, users
from app.api.dependencies import AsyncSessionLocal

# Import debug router if in debug mode
if settings.debug:
    from app.api import debug


# Configure logging based on settings
if settings.log_format == "json":
    import structlog
    from app.core.logging_processors import (
        mask_pii_processor,
        compliance_processor,
        security_processor,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            mask_pii_processor,  # ← Add PII masking
            compliance_processor,  # ← Add compliance metadata
            security_processor,  # ← Add security alerts
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger(__name__)
else:
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)


# Create the FastAPI application
app = create_app()


# Include API routers
app.include_router(
    accounts.router,
    prefix=f"{settings.api_v1_str}/accounts",
    tags=["accounts"],
)

app.include_router(
    transactions.router,
    prefix=(f"{settings.api_v1_str}/accounts"),
    tags=["transactions"],
)

app.include_router(
    users.router,
    prefix=f"{settings.api_v1_str}/users",
    tags=["users"],
)

# Include debug router if in debug mode
if settings.debug:
    app.include_router(debug.router, tags=["debug"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "service": settings.project_name,
            "version": settings.version,
            "environment": settings.environment,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": settings.project_name,
                "version": settings.version,
                "environment": settings.environment,
                "error": str(e),
            },
        )


@app.get("/")
async def root():
    """Root endpoint."""
    # Add a test variable for breakpoint testing
    test_variable = "This is a test for debugging"
    print(f"🐛 DEBUG: Root endpoint called - {test_variable}")

    return {
        "service": settings.project_name,
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
        "debug_test": test_variable,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
