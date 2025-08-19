"""Custom FastAPI application with enhanced functionality."""

from typing import Type, Callable, Any, Dict, Optional
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog
import time
import uuid

from .config import settings
from .events import EventBus
from ..api.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
)


logger = structlog.get_logger(__name__)


class EagleBankFastAPI(FastAPI):
    """Enhanced FastAPI application with custom functionality."""

    def __init__(self, *args, **kwargs):
        """Initialize with custom defaults."""
        # Set default values
        kwargs.setdefault("title", settings.project_name)
        kwargs.setdefault("version", settings.version)
        kwargs.setdefault("debug", settings.debug)
        kwargs.setdefault("lifespan", self.lifespan)

        super().__init__(*args, **kwargs)

        # Initialize event bus
        self.event_bus: Optional[EventBus] = None

        # Setup middleware
        self._setup_middleware()

        # Setup exception handlers
        self._setup_exception_handlers()

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Application lifespan context manager."""
        # Startup
        logger.info("Starting Eagle Bank API", debug=settings.debug)

        # Initialize event bus
        self.event_bus = EventBus()
        await self.event_bus.initialize()

        # Store event bus in app state
        self.state.event_bus = self.event_bus

        logger.info(
            "Eagle Bank API started successfully",
            event_bus_initialized=bool(self.event_bus),
        )
        yield

        # Shutdown
        logger.info("Shutting down Eagle Bank API")

        if self.event_bus:
            await self.event_bus.close()
            logger.debug("Event bus closed successfully")

        logger.info("Eagle Bank API shutdown complete")

    def _setup_middleware(self):
        """Setup application middleware."""
        # CORS middleware
        self.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Trusted host middleware
        self.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts,
        )
        # Custom middleware
        self.add_middleware(SecurityHeadersMiddleware)
        self.add_middleware(RateLimitMiddleware)
        self.add_middleware(RequestLoggingMiddleware)

    def _setup_exception_handlers(self):
        """Setup custom exception handlers."""
        from fastapi import HTTPException
        from fastapi.responses import JSONResponse

        @self.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """Handle HTTP exceptions with structured logging."""
            logger.warning(
                "HTTP exception occurred",
                status_code=exc.status_code,
                detail=exc.detail,
                path=request.url.path,
                method=request.method,
            )

            return JSONResponse(
                status_code=exc.status_code, content={"message": exc.detail}
            )

        @self.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Handle general exceptions with structured logging."""
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

            logger.error(
                "Unhandled exception occurred",
                exc_info=exc,
                request_id=request_id,
                path=request.url.path,
                method=request.method,
            )

            return JSONResponse(
                status_code=500,
                content={
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                },
            )

    async def publish_event(self, event_name: str, data: Dict[str, Any]):
        """Publish an event through the event bus."""
        if self.event_bus:
            await self.event_bus.publish(event_name, data)

    async def subscribe_to_event(self, event_name: str, handler: Callable):
        """Subscribe to an event through the event bus."""
        if self.event_bus:
            await self.event_bus.subscribe(event_name, handler)


def create_app() -> EagleBankFastAPI:
    """Factory function to create FastAPI application."""
    app = EagleBankFastAPI(
        title=settings.project_name,
        version=settings.version,
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    return app
