"""Security utilities and decorators."""

from typing import Optional, Dict, Any, List
from functools import wraps
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import hashlib
import hmac

from .config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityUtils:
    """Security utility functions."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generate a JWT token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_account_number() -> str:
        """Generate a bank account number."""
        # Format: 01XXXXXX (8 digits total, starting with 01)
        random_part = secrets.randbelow(1000000)
        return f"01{random_part:06d}"
    
    @staticmethod
    def generate_transaction_id() -> str:
        """Generate a transaction ID."""
        # Format: tan-XXXXXXX
        random_part = secrets.token_hex(6)
        return f"tan-{random_part}"
    
    @staticmethod
    def generate_user_id() -> str:
        """Generate a user ID."""
        # Format: usr-XXXXXXX
        random_part = secrets.token_hex(6)
        return f"usr-{random_part}"
    
    @staticmethod
    def validate_account_number(account_number: str) -> bool:
        """Validate account number format."""
        import re
        pattern = r"^01\d{6}$"
        return bool(re.match(pattern, account_number))
    
    @staticmethod
    def validate_transaction_id(transaction_id: str) -> bool:
        """Validate transaction ID format."""
        import re
        pattern = r"^tan-[A-Za-z0-9]+$"
        return bool(re.match(pattern, transaction_id))
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate user ID format."""
        import re
        pattern = r"^usr-[A-Za-z0-9]+$"
        return bool(re.match(pattern, user_id))
    
    @staticmethod
    def create_signature(data: str, secret: str) -> str:
        """Create HMAC signature for data."""
        return hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_signature(data: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature."""
        expected_signature = SecurityUtils.create_signature(data, secret)
        return hmac.compare_digest(expected_signature, signature)
    
    @staticmethod
    def sanitize_input(value: str, allowed_chars: str = None) -> str:
        """Sanitize user input."""
        if allowed_chars is None:
            # Default allowed characters for general text
            allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .-_@"
        
        return ''.join(char for char in value if char in allowed_chars)


def rate_limit(calls_per_minute: int = 60):
    """Decorator for rate limiting function calls."""
    call_times: Dict[str, List[datetime]] = {}
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Use function name as key (in real implementation, use user ID)
            key = func.__name__
            now = datetime.utcnow()
            
            # Initialize if not exists
            if key not in call_times:
                call_times[key] = []
            
            # Remove old calls
            minute_ago = now - timedelta(minutes=1)
            call_times[key] = [
                call_time for call_time in call_times[key]
                if call_time > minute_ago
            ]
            
            # Check limit
            if len(call_times[key]) >= calls_per_minute:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
            
            # Record this call
            call_times[key].append(now)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permissions(permissions: List[str]):
    """Decorator to require specific permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break
            
            if not request:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=500,
                    detail="Internal error: Request not found"
                )
            
            # Check user permissions
            user_permissions = getattr(request.state, 'user_permissions', [])
            
            for permission in permissions:
                if permission not in user_permissions:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=403,
                        detail=f"Permission required: {permission}"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def audit_log(action: str):
    """Decorator to log user actions for audit purposes."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user info
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break
            
            user_id = getattr(request.state, 'user_id', 'anonymous') if request else 'unknown'
            
            # Log the action
            import logging
            audit_logger = logging.getLogger('audit')
            audit_logger.info(
                f"User {user_id} performed action: {action}",
                extra={
                    'user_id': user_id,
                    'action': action,
                    'timestamp': datetime.utcnow().isoformat(),
                    'function': func.__name__
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # Log success
                audit_logger.info(
                    f"Action {action} completed successfully for user {user_id}"
                )
                
                return result
                
            except Exception as e:
                # Log failure
                audit_logger.error(
                    f"Action {action} failed for user {user_id}: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator
