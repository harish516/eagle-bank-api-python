"""Debug utilities for Eagle Bank API."""

import inspect
import json
import time
from typing import Any, Dict, Optional
from functools import wraps
import structlog
from fastapi import Request, Response

logger = structlog.get_logger(__name__)


def debug_function(func_name: Optional[str] = None):
    """Decorator to debug function calls with parameters and return values."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            # Log function entry
            logger.debug(
                "Function called",
                function=name,
                args=str(args)[:200],  # Truncate long args
                kwargs={k: str(v)[:100] for k, v in kwargs.items()},
                timestamp=start_time
            )
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful completion
                logger.debug(
                    "Function completed successfully",
                    function=name,
                    execution_time_ms=round(execution_time * 1000, 2),
                    result_type=type(result).__name__
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log exception
                logger.error(
                    "Function failed with exception",
                    function=name,
                    execution_time_ms=round(execution_time * 1000, 2),
                    exception=str(e),
                    exception_type=type(e).__name__,
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            # Log function entry
            logger.debug(
                "Function called",
                function=name,
                args=str(args)[:200],
                kwargs={k: str(v)[:100] for k, v in kwargs.items()},
                timestamp=start_time
            )
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful completion
                logger.debug(
                    "Function completed successfully",
                    function=name,
                    execution_time_ms=round(execution_time * 1000, 2),
                    result_type=type(result).__name__
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log exception
                logger.error(
                    "Function failed with exception",
                    function=name,
                    execution_time_ms=round(execution_time * 1000, 2),
                    exception=str(e),
                    exception_type=type(e).__name__,
                    exc_info=True
                )
                raise
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def debug_request(request: Request) -> Dict[str, Any]:
    """Extract debug information from a FastAPI request."""
    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "client_host": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", "Unknown"),
        "content_type": request.headers.get("content-type", "Unknown"),
        "request_id": getattr(request.state, "request_id", "Unknown")
    }


def debug_response(response: Response) -> Dict[str, Any]:
    """Extract debug information from a FastAPI response."""
    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "media_type": getattr(response, "media_type", "Unknown")
    }


def log_database_query(query: str, params: Optional[Dict] = None, execution_time: Optional[float] = None):
    """Log database queries for debugging."""
    logger.debug(
        "Database query executed",
        query=query,
        params=params,
        execution_time_ms=round(execution_time * 1000, 2) if execution_time else None
    )


def log_redis_operation(operation: str, key: Optional[str] = None, value: Optional[Any] = None, 
                       execution_time: Optional[float] = None):
    """Log Redis operations for debugging."""
    logger.debug(
        "Redis operation executed",
        operation=operation,
        key=key,
        value_type=type(value).__name__ if value else None,
        execution_time_ms=round(execution_time * 1000, 2) if execution_time else None
    )


def log_event_bus_activity(event_name: str, data: Dict[str, Any], operation: str = "publish"):
    """Log event bus activity for debugging."""
    logger.debug(
        f"Event bus {operation}",
        event_name=event_name,
        data_keys=list(data.keys()) if data else [],
        data_size=len(json.dumps(data)) if data else 0
    )


class DebugMiddleware:
    """Middleware for detailed request/response debugging."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Create request object for debugging
            request = Request(scope, receive)
            start_time = time.time()
            
            # Log request details
            logger.debug(
                "Incoming request",
                **debug_request(request),
                timestamp=start_time
            )
            
            # Track response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    execution_time = time.time() - start_time
                    logger.debug(
                        "Response sent",
                        status_code=message["status"],
                        execution_time_ms=round(execution_time * 1000, 2),
                        headers={k.decode(): v.decode() for k, v in message.get("headers", [])}
                    )
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


def enable_sqlalchemy_logging():
    """Enable SQLAlchemy query logging for debugging."""
    import logging
    
    # Enable SQLAlchemy logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)


def setup_debug_environment():
    """Setup comprehensive debugging environment."""
    from .config import settings
    
    if settings.debug:
        # Enable all debug logging
        enable_sqlalchemy_logging()
        
        logger.info(
            "Debug environment enabled",
            log_level=settings.log_level,
            debug_mode=settings.debug,
            environment=settings.environment
        )
