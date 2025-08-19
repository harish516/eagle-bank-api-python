"""Authentication module initialization."""

from .keycloak import keycloak_client, keycloak_adapter, KeycloakClient, KeycloakAdapter
from .decorators import (
    authenticate_token,
    require_authentication,
    require_roles,
    require_permissions,
    optional_authentication,
    AuthenticatedUser,
    authenticated_user,
    admin_user,
    manager_user,
    customer_user
)
from .context import (
    get_current_user,
    set_current_user,
    get_current_token,
    set_current_token,
    get_current_permissions,
    set_current_permissions,
    get_user_id,
    get_user_email,
    get_user_name,
    has_permission,
    has_any_permission,
    has_all_permissions,
    UserContext,
    get_user_context,
    run_with_user_context
)

__all__ = [
    # Keycloak
    "keycloak_client",
    "keycloak_adapter",
    "KeycloakClient",
    "KeycloakAdapter",
    
    # Decorators
    "authenticate_token",
    "require_authentication",
    "require_roles",
    "require_permissions",
    "optional_authentication",
    "AuthenticatedUser",
    "authenticated_user",
    "admin_user",
    "manager_user",
    "customer_user",
    
    # Context
    "get_current_user",
    "set_current_user",
    "get_current_token", 
    "set_current_token",
    "get_current_permissions",
    "set_current_permissions",
    "get_user_id",
    "get_user_email",
    "get_user_name",
    "has_permission",
    "has_any_permission",
    "has_all_permissions",
    "UserContext",
    "get_user_context",
    "run_with_user_context"
]
