"""OpenTelemetry configuration for Eagle Bank API."""

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
import structlog

logger = structlog.get_logger(__name__)


def setup_telemetry(app_name: str = "eagle-bank-api"):
    """Configure OpenTelemetry for the application."""

    # 1. Setup Tracing
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)

    # Add console exporter for development (replace with proper exporter in production)
    span_processor = BatchSpanProcessor(ConsoleSpanExporter())
    trace.get_tracer_provider().add_span_processor(span_processor)

    # 2. Setup Metrics
    metric_reader = PeriodicExportingMetricReader(
        ConsoleMetricExporter(), export_interval_millis=5000
    )
    metrics.set_meter_provider(MeterProvider(metric_readers=[metric_reader]))
    meter = metrics.get_meter(__name__)

    logger.info("OpenTelemetry configured successfully", app_name=app_name)

    return tracer, meter


def instrument_fastapi(app):
    """Instrument FastAPI application with OpenTelemetry."""

    # Automatically instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        server_request_hook=server_request_hook,
        client_request_hook=client_request_hook,
    )

    # Instrument other libraries
    HTTPXClientInstrumentor().instrument()  # HTTP client calls
    RedisInstrumentor().instrument()  # Redis operations
    SQLAlchemyInstrumentor().instrument()  # Database operations

    logger.info("FastAPI application instrumented with OpenTelemetry")


def server_request_hook(span, scope):
    """Custom hook for incoming requests."""
    if span and span.is_recording():
        # Add custom attributes to spans
        span.set_attribute("eagle_bank.service", "api")
        span.set_attribute("eagle_bank.version", "1.0.0")


def client_request_hook(span, request):
    """Custom hook for outgoing requests."""
    if span and span.is_recording():
        span.set_attribute("eagle_bank.client", "httpx")


# Custom metrics for business logic
class EagleBankMetrics:
    """Custom business metrics for Eagle Bank API."""

    def __init__(self, meter):
        self.meter = meter

        # Business metrics
        self.account_operations = meter.create_counter(
            "eagle_bank_account_operations_total",
            description="Total account operations",
            unit="1",
        )

        self.transaction_amount = meter.create_histogram(
            "eagle_bank_transaction_amount",
            description="Transaction amounts",
            unit="currency",
        )

        self.active_users = meter.create_up_down_counter(
            "eagle_bank_active_users", description="Currently active users", unit="1"
        )

        self.balance_check_duration = meter.create_histogram(
            "eagle_bank_balance_check_duration_seconds",
            description="Time spent checking account balances",
            unit="s",
        )

    def record_account_operation(self, operation_type: str, success: bool = True):
        """Record an account operation."""
        self.account_operations.add(
            1,
            {
                "operation": operation_type,
                "status": "success" if success else "failure",
            },
        )

    def record_transaction(self, amount: float, transaction_type: str):
        """Record a transaction."""
        self.transaction_amount.record(amount, {"type": transaction_type})

    def increment_active_users(self):
        """Increment active user count."""
        self.active_users.add(1)

    def decrement_active_users(self):
        """Decrement active user count."""
        self.active_users.add(-1)

    def record_balance_check_duration(self, duration: float):
        """Record balance check duration."""
        self.balance_check_duration.record(duration)
