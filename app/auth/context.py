"""Authentication context management using context variables."""

from typing import Optional, Dict, Any
from contextvars import ContextVar
import asyncio


# Context variables for user authentication
_current_user: ContextVar[Optional[Dict[str, Any]]] = ContextVar('current_user', default=None)
_current_token: ContextVar[Optional[str]] = ContextVar('current_token', default=None)
_current_permissions: ContextVar[Optional[list]] = ContextVar('current_permissions', default=None)


async def set_current_user(user_info: Optional[Dict[str, Any]]) -> None:
    """Set the current user in context."""
    _current_user.set(user_info)


async def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the current user from context."""
    return _current_user.get()


async def set_current_token(token: Optional[str]) -> None:
    """Set the current token in context."""
    _current_token.set(token)


async def get_current_token() -> Optional[str]:
    """Get the current token from context."""
    return _current_token.get()


async def set_current_permissions(permissions: Optional[list]) -> None:
    """Set the current user permissions in context."""
    _current_permissions.set(permissions)


async def get_current_permissions() -> Optional[list]:
    """Get the current user permissions from context."""
    return _current_permissions.get()


async def get_user_id() -> Optional[str]:
    """Get the current user ID."""
    user = await get_current_user()
    return user.get('sub') if user else None


async def get_user_email() -> Optional[str]:
    """Get the current user email."""
    user = await get_current_user()
    return user.get('email') if user else None


async def get_user_name() -> Optional[str]:
    """Get the current user name."""
    user = await get_current_user()
    if user:
        return user.get('name') or f"{user.get('given_name', '')} {user.get('family_name', '')}".strip()
    return None


async def has_permission(permission: str) -> bool:
    """Check if current user has a specific permission."""
    permissions = await get_current_permissions()
    return permission in permissions if permissions else False


async def has_any_permission(permissions: list) -> bool:
    """Check if current user has any of the specified permissions."""
    user_permissions = await get_current_permissions()
    if not user_permissions:
        return False
    
    return any(perm in user_permissions for perm in permissions)


async def has_all_permissions(permissions: list) -> bool:
    """Check if current user has all of the specified permissions."""
    user_permissions = await get_current_permissions()
    if not user_permissions:
        return False
    
    return all(perm in user_permissions for perm in permissions)


class UserContext:
    """Context manager for user authentication context."""
    
    def __init__(self, user_info: Dict[str, Any], token: str = None, permissions: list = None):
        self.user_info = user_info
        self.token = token
        self.permissions = permissions or []
        
        # Store previous values
        self.prev_user = None
        self.prev_token = None
        self.prev_permissions = None
    
    async def __aenter__(self):
        """Enter the context."""
        # Store previous values
        self.prev_user = _current_user.get()
        self.prev_token = _current_token.get()
        self.prev_permissions = _current_permissions.get()
        
        # Set new values
        await set_current_user(self.user_info)
        if self.token:
            await set_current_token(self.token)
        if self.permissions:
            await set_current_permissions(self.permissions)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        # Restore previous values
        await set_current_user(self.prev_user)
        await set_current_token(self.prev_token)
        await set_current_permissions(self.prev_permissions)


async def get_user_context() -> Dict[str, Any]:
    """Get complete user context."""
    return {
        'user': await get_current_user(),
        'token': await get_current_token(),
        'permissions': await get_current_permissions(),
        'user_id': await get_user_id(),
        'email': await get_user_email(),
        'name': await get_user_name()
    }


def run_with_user_context(user_info: Dict[str, Any], token: str = None, 
                         permissions: list = None):
    """Decorator to run function with user context."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with UserContext(user_info, token, permissions):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
