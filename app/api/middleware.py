"""Custom middleware for the FastAPI application."""

from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import uuid
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import logging

# Configure basic logging for middleware
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            (
                f"Request started - {request.method} {request.url.path} "
                f"[{request_id}]"
            )
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed - {request.method} {request.url.path} "
                f"[{request_id}] - {response.status_code} - {duration:.3f}s"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            logger.error(
                f"Request failed - {request.method} {request.url.path} "
                f"[{request_id}] - {duration:.3f}s - {str(e)}"
            )

            # Re-raise the exception
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app, calls_per_minute: int = 100):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.client_calls: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on client IP."""
        # Get client IP
        client_ip = self._get_client_ip(request)

        # Get current time
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Clean old entries
        self.client_calls[client_ip] = [
            call_time
            for call_time in self.client_calls[client_ip]
            if call_time > minute_ago
        ]

        # Check rate limit
        if len(self.client_calls[client_ip]) >= self.calls_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        # Record this call
        self.client_calls[client_ip].append(now)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, self.calls_per_minute - len(self.client_calls[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int((now + timedelta(minutes=1)).timestamp())
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Circuit breaker pattern implementation."""

    def __init__(self, app, failure_threshold: int = 5, timeout: int = 60):
        super().__init__(app)
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: datetime = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply circuit breaker pattern."""
        # Check if circuit is open
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                return JSONResponse(
                    status_code=503,
                    content={
                        "message": "Service temporarily unavailable. Circuit breaker is open.",
                        "retry_after": self.timeout,
                    },
                )

        try:
            # Process request
            response = await call_next(request)

            # Check if response indicates failure
            if response.status_code >= 500:
                await self._record_failure()
            else:
                await self._record_success()

            return response

        except Exception as e:
            await self._record_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True

        return (datetime.utcnow() - self.last_failure_time).seconds >= self.timeout

    async def _record_failure(self):
        """Record a failure and update circuit breaker state."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    async def _record_success(self):
        """Record a success and reset failure count."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker closed after successful request")

        self.failure_count = 0
        self.last_failure_time = None


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting metrics."""

    def __init__(self, app):
        super().__init__(app)
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(list)
        self.error_count = defaultdict(int)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect request metrics."""
        start_time = time.time()
        method_path = f"{request.method} {request.url.path}"

        try:
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            self.request_count[method_path] += 1
            self.request_duration[method_path].append(duration)

            if response.status_code >= 400:
                self.error_count[method_path] += 1

            # Add metrics headers
            response.headers["X-Response-Time"] = f"{duration:.3f}"

            return response

        except Exception:
            # Record error
            duration = time.time() - start_time
            self.error_count[method_path] += 1
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        metrics = {
            "request_count": dict(self.request_count),
            "error_count": dict(self.error_count),
            "average_duration": {},
        }

        # Calculate average durations
        for path, durations in self.request_duration.items():
            if durations:
                metrics["average_duration"][path] = sum(durations) / len(durations)

        return metrics
