"""Debug endpoints for development and troubleshooting."""

from fastapi import APIRouter, Depends, Request
from typing import Dict, Any
import sys
import os
import psutil
from datetime import datetime
from sqlalchemy import text

from ..core.config import settings
from ..api.dependencies import get_database, AsyncSessionLocal
from ..core.debug import debug_request

# Only enable debug endpoints in debug mode
if settings.debug:
    router = APIRouter(prefix="/debug", tags=["debug"])
    
    @router.get("/info")
    async def debug_info():
        """Get system and application debug information."""
        return {
            "application": {
                "name": settings.project_name,
                "version": settings.version,
                "environment": settings.environment,
                "debug_mode": settings.debug,
                "log_level": settings.log_level
            },
            "system": {
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": psutil.cpu_count(),
                "memory_usage": psutil.virtual_memory()._asdict(),
                "disk_usage": psutil.disk_usage("/")._asdict() if os.name != "nt" else None
            },
            "process": {
                "pid": os.getpid(),
                "memory_info": psutil.Process().memory_info()._asdict(),
                "cpu_percent": psutil.Process().cpu_percent(),
                "create_time": datetime.fromtimestamp(psutil.Process().create_time()).isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    @router.get("/request")
    async def debug_request_info(request: Request):
        """Get detailed information about the current request."""
        return {
            "request_details": debug_request(request),
            "state": dict(request.state.__dict__) if hasattr(request, 'state') else {},
            "timestamp": datetime.now().isoformat()
        }
    
    @router.get("/database")
    async def debug_database():
        """Test database connectivity and get connection info."""
        try:
            async with AsyncSessionLocal() as session:
                # Test basic query
                result = await session.execute(text("SELECT version(), current_database(), current_user"))
                row = result.fetchone()
                
                return {
                    "status": "connected",
                    "database_version": row[0] if row else None,
                    "current_database": row[1] if row else None,
                    "current_user": row[2] if row else None,
                    "connection_url": settings.database_url.split("@")[1] if "@" in settings.database_url else "hidden",
                    "pool_size": settings.database_pool_size,
                    "max_overflow": settings.database_max_overflow,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
    
    @router.get("/redis")
    async def debug_redis():
        """Test Redis connectivity and get connection info."""
        try:
            import redis.asyncio as aioredis
            
            redis_client = aioredis.from_url(settings.redis_url)
            
            # Test basic operations
            await redis_client.ping()
            await redis_client.set("debug_test", "test_value", ex=10)
            value = await redis_client.get("debug_test")
            await redis_client.delete("debug_test")
            
            info = await redis_client.info()
            await redis_client.close()
            
            return {
                "status": "connected",
                "test_operation": "success" if value == b"test_value" else "failed",
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "connection_url": settings.redis_url.split("@")[1] if "@" in settings.redis_url else settings.redis_url,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
    
    @router.get("/config")
    async def debug_config():
        """Get sanitized configuration for debugging."""
        config_dict = {}
        for key, value in settings.__dict__.items():
            if not key.startswith("_"):
                # Sanitize sensitive information
                if any(sensitive in key.lower() for sensitive in ["password", "secret", "key", "token"]):
                    config_dict[key] = "***HIDDEN***"
                elif "url" in key.lower() and "@" in str(value):
                    # Hide credentials in URLs
                    config_dict[key] = str(value).split("@")[1] if "@" in str(value) else str(value)
                else:
                    config_dict[key] = value
        
        return {
            "configuration": config_dict,
            "timestamp": datetime.now().isoformat()
        }
    
    @router.post("/test-error")
    async def test_error_handling():
        """Endpoint to test error handling and logging."""
        raise Exception("This is a test exception for debugging purposes")
    
    @router.get("/logs/recent")
    async def get_recent_logs():
        """Get recent log entries (if file logging is enabled)."""
        if not settings.log_to_file or not os.path.exists(settings.log_file_path):
            return {"error": "File logging not enabled or log file not found"}
        
        try:
            with open(settings.log_file_path, 'r') as f:
                lines = f.readlines()
                # Return last 50 lines
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                
            return {
                "total_lines": len(lines),
                "recent_lines": len(recent_lines),
                "logs": [line.strip() for line in recent_lines],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }

else:
    # Create empty router if not in debug mode
    router = APIRouter()
