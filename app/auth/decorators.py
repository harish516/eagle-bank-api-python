"""Authentication decorators and utilities."""

from typing import Optional, List, Callable, Any
from functools import wraps
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from .keycloak import keycloak_adapter
from .context import get_current_user, set_current_user, get_user_context


logger = logging.getLogger(__name__)
security = HTTPBearer()


def authenticate_token(token: str = Depends(security)) -> dict:
    """Dependency to authenticate JWT token."""
    async def _authenticate():
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Authorization header missing"
            )
        
        user_info = await keycloak_adapter.authenticate_user(token.credentials)
        if not user_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        return user_info
    
    return _authenticate


def require_authentication(func: Callable) -> Callable:
    """Decorator to require authentication."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the request object in arguments
        request: Optional[Request] = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            raise HTTPException(
                status_code=500,
                detail="Request object not found"
            )
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Authorization header missing or invalid"
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Validate token
        user_info = await keycloak_adapter.authenticate_user(token)
        if not user_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        # Set user context
        await set_current_user(user_info)
        request.state.user = user_info
        request.state.token = token
        
        # Get user permissions
        permissions = await keycloak_adapter.get_user_permissions(token)
        request.state.permissions = permissions
        
        try:
            return await func(*args, **kwargs)
        finally:
            # Clear user context after request
            await set_current_user(None)
    
    return wrapper


def require_roles(roles: List[str]) -> Callable:
    """Decorator to require specific roles."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=500,
                    detail="Request object not found"
                )
            
            # Check if user is authenticated
            if not hasattr(request.state, 'token'):
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # Check roles
            token = request.state.token
            user_authorized = await keycloak_adapter.authorize_user(token, roles)
            
            if not user_authorized:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required roles: {', '.join(roles)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permissions(permissions: List[str]) -> Callable:
    """Decorator to require specific permissions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=500,
                    detail="Request object not found"
                )
            
            # Check if user is authenticated
            if not hasattr(request.state, 'permissions'):
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            user_permissions = request.state.permissions
            
            # Check if user has all required permissions
            missing_permissions = [
                perm for perm in permissions 
                if perm not in user_permissions
            ]
            
            if missing_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Missing: {', '.join(missing_permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def optional_authentication(func: Callable) -> Callable:
    """Decorator for optional authentication."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the request object
        request: Optional[Request] = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if request:
            # Try to authenticate if token is present
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    user_info = await keycloak_adapter.authenticate_user(token)
                    if user_info:
                        await set_current_user(user_info)
                        request.state.user = user_info
                        request.state.token = token
                        
                        # Get permissions
                        permissions = await keycloak_adapter.get_user_permissions(token)
                        request.state.permissions = permissions
                except Exception as e:
                    logger.warning(f"Optional authentication failed: {e}")
                    # Continue without authentication
                    pass
        
        try:
            return await func(*args, **kwargs)
        finally:
            # Clear user context if set
            if request and hasattr(request.state, 'user'):
                await set_current_user(None)
    
    return wrapper


class AuthenticatedUser:
    """Dependency class for getting authenticated user."""
    
    def __init__(self, required_roles: List[str] = None, 
                 required_permissions: List[str] = None):
        self.required_roles = required_roles or []
        self.required_permissions = required_permissions or []
    
    async def __call__(self, request: Request) -> dict:
        """Get authenticated user with optional role/permission checks."""
        # Check authentication
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Authorization header missing or invalid"
            )
        
        token = auth_header[7:]
        
        # Validate token
        user_info = await keycloak_adapter.authenticate_user(token)
        if not user_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        # Check roles if required
        if self.required_roles:
            user_authorized = await keycloak_adapter.authorize_user(token, self.required_roles)
            if not user_authorized:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required roles: {', '.join(self.required_roles)}"
                )
        
        # Check permissions if required
        if self.required_permissions:
            user_permissions = await keycloak_adapter.get_user_permissions(token)
            missing_permissions = [
                perm for perm in self.required_permissions 
                if perm not in user_permissions
            ]
            
            if missing_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Missing: {', '.join(missing_permissions)}"
                )
        
        # Set context
        await set_current_user(user_info)
        request.state.user = user_info
        request.state.token = token
        
        return user_info


# Convenience instances
authenticated_user = AuthenticatedUser()
admin_user = AuthenticatedUser(required_roles=["bank-admin"])
manager_user = AuthenticatedUser(required_roles=["account-manager", "bank-admin"])
customer_user = AuthenticatedUser(required_roles=["customer", "account-manager", "bank-admin"])
