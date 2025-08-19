"""Enhanced middleware with OpenTelemetry integration."""

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import time

tracer = trace.get_tracer(__name__)


class EnhancedRequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware enhanced with OpenTelemetry."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get current span created by FastAPI instrumentation
        current_span = trace.get_current_span()

        # Add custom attributes to the span
        if current_span.is_recording():
            current_span.set_attribute(
                "eagle_bank.request_id", getattr(request.state, "request_id", "unknown")
            )
            current_span.set_attribute(
                "eagle_bank.client_ip",
                request.client.host if request.client else "unknown",
            )
            current_span.set_attribute(
                "eagle_bank.user_agent", request.headers.get("user-agent", "unknown")
            )

        try:
            response = await call_next(request)

            # Mark span as successful
            if current_span.is_recording():
                current_span.set_status(Status(StatusCode.OK))
                current_span.set_attribute(
                    "http.response.status_code", response.status_code
                )

            return response

        except Exception as e:
            # Mark span as error
            if current_span.is_recording():
                current_span.set_status(Status(StatusCode.ERROR, str(e)))
                current_span.record_exception(e)
            raise


class EnhancedCircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Circuit breaker with OpenTelemetry integration."""

    def __init__(self, app, failure_threshold: int = 5, timeout: int = 60):
        super().__init__(app)
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.state = "CLOSED"

        # Create custom metrics
        from opentelemetry import metrics

        meter = metrics.get_meter(__name__)

        self.circuit_breaker_state = meter.create_up_down_counter(
            "eagle_bank_circuit_breaker_state",
            description="Circuit breaker state (0=closed, 1=open, 2=half-open)",
        )

        self.circuit_breaker_failures = meter.create_counter(
            "eagle_bank_circuit_breaker_failures_total",
            description="Total circuit breaker failures",
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        # Create custom span for circuit breaker logic
        with tracer.start_as_current_span("circuit_breaker_check") as span:
            span.set_attribute("circuit_breaker.state", self.state)
            span.set_attribute("circuit_breaker.failure_count", self.failure_count)

            if self.state == "OPEN":
                span.set_attribute("circuit_breaker.action", "blocked")
                span.set_status(Status(StatusCode.ERROR, "Circuit breaker open"))

                # Record metric
                self.circuit_breaker_state.add(1, {"state": "open"})

                return JSONResponse(
                    status_code=503,
                    content={"message": "Service temporarily unavailable"},
                )

            try:
                response = await call_next(request)

                if response.status_code >= 500:
                    await self._record_failure(span)
                else:
                    await self._record_success(span)

                return response

            except Exception as e:
                await self._record_failure(span)
                raise

    async def _record_failure(self, span):
        """Record failure with telemetry."""
        self.failure_count += 1

        # Add to span
        span.set_attribute("circuit_breaker.failure_recorded", True)
        span.set_attribute("circuit_breaker.new_failure_count", self.failure_count)

        # Record metric
        self.circuit_breaker_failures.add(1)

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            span.set_attribute("circuit_breaker.opened", True)
            self.circuit_breaker_state.add(1, {"state": "open"})

    async def _record_success(self, span):
        """Record success with telemetry."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            span.set_attribute("circuit_breaker.closed", True)
            self.circuit_breaker_state.add(-1, {"state": "closed"})

        self.failure_count = 0
