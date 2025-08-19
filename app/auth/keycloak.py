"""Keycloak authentication integration."""

from typing import Optional, Dict, Any, List
import httpx
import json
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging

from ..core.config import settings


logger = logging.getLogger(__name__)


class KeycloakError(Exception):
    """Base exception for Keycloak operations."""
    pass


class KeycloakAuthenticationError(KeycloakError):
    """Authentication-related errors."""
    pass


class KeycloakAuthorizationError(KeycloakError):
    """Authorization-related errors."""
    pass


class KeycloakClient:
    """Keycloak client for authentication and authorization."""
    
    def __init__(self):
        self.server_url = settings.keycloak_server_url
        self.realm = settings.keycloak_realm
        self.client_id = settings.keycloak_client_id
        self.client_secret = settings.keycloak_client_secret
        
        # URLs
        self.realm_url = f"{self.server_url}/realms/{self.realm}"
        self.auth_url = f"{self.realm_url}/protocol/openid-connect/auth"
        self.token_url = f"{self.realm_url}/protocol/openid-connect/token"
        self.userinfo_url = f"{self.realm_url}/protocol/openid-connect/userinfo"
        self.certs_url = f"{self.realm_url}/protocol/openid-connect/certs"
        
        # Admin URLs
        self.admin_url = f"{self.server_url}/admin/realms/{self.realm}"
        
        self._admin_token: Optional[str] = None
        self._admin_token_expires: Optional[datetime] = None
        self._public_keys: Optional[Dict[str, Any]] = None
        self._public_keys_expires: Optional[datetime] = None
    
    async def get_admin_token(self) -> str:
        """Get admin access token for Keycloak management operations."""
        # Check if current token is still valid
        if (self._admin_token and self._admin_token_expires and 
            datetime.utcnow() < self._admin_token_expires - timedelta(minutes=5)):
            return self._admin_token
        
        # Request new admin token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": "admin-cli",
                    "username": settings.keycloak_admin_username,
                    "password": settings.keycloak_admin_password
                }
            )
        
        if response.status_code != 200:
            raise KeycloakAuthenticationError(
                f"Failed to get admin token: {response.text}"
            )
        
        token_data = response.json()
        self._admin_token = token_data["access_token"]
        self._admin_token_expires = datetime.utcnow() + timedelta(
            seconds=token_data.get("expires_in", 300)
        )
        
        return self._admin_token
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token with Keycloak."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.userinfo_url,
                    headers={"Authorization": f"Bearer {token}"}
                )
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None
    
    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from token."""
        return await self.validate_token(token)
    
    async def get_user_roles(self, token: str) -> List[str]:
        """Extract user roles from token."""
        try:
            # Decode token (simplified - in production use proper JWT validation)
            import base64
            import json
            
            # Split token and decode payload
            parts = token.split('.')
            if len(parts) != 3:
                return []
            
            # Add padding if needed
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            
            # Decode
            decoded = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded)
            
            # Extract roles
            roles = []
            
            # Realm roles
            if 'realm_access' in payload_data:
                roles.extend(payload_data['realm_access'].get('roles', []))
            
            # Client roles
            if 'resource_access' in payload_data and self.client_id in payload_data['resource_access']:
                roles.extend(payload_data['resource_access'][self.client_id].get('roles', []))
            
            return roles
            
        except Exception as e:
            logger.error(f"Failed to extract roles: {e}")
            return []
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a user in Keycloak."""
        admin_token = await self.get_admin_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.admin_url}/users",
                headers={
                    "Authorization": f"Bearer {admin_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "username": user_data["email"],
                    "email": user_data["email"],
                    "firstName": user_data.get("firstName", ""),
                    "lastName": user_data.get("lastName", ""),
                    "enabled": True,
                    "emailVerified": True,
                    "credentials": [{
                        "type": "password",
                        "value": user_data.get("password", ""),
                        "temporary": False
                    }] if "password" in user_data else []
                }
            )
        
        if response.status_code not in [201, 409]:  # 409 = user already exists
            raise KeycloakError(f"Failed to create user: {response.text}")
        
        # Extract user ID from location header
        if response.status_code == 201:
            location = response.headers.get("Location", "")
            user_id = location.split("/")[-1]
            return user_id
        
        # If user exists, get user ID
        return await self.get_user_id_by_email(user_data["email"])
    
    async def get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get user ID by email."""
        admin_token = await self.get_admin_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.admin_url}/users",
                headers={"Authorization": f"Bearer {admin_token}"},
                params={"email": email}
            )
        
        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0]["id"]
        
        return None
    
    async def assign_role_to_user(self, user_id: str, role_name: str):
        """Assign a role to a user."""
        admin_token = await self.get_admin_token()
        
        # First, get role representation
        async with httpx.AsyncClient() as client:
            role_response = await client.get(
                f"{self.admin_url}/roles/{role_name}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        
        if role_response.status_code != 200:
            raise KeycloakError(f"Role {role_name} not found")
        
        role_data = role_response.json()
        
        # Assign role to user
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.admin_url}/users/{user_id}/role-mappings/realm",
                headers={
                    "Authorization": f"Bearer {admin_token}",
                    "Content-Type": "application/json"
                },
                json=[role_data]
            )
        
        if response.status_code not in [204, 200]:
            raise KeycloakError(f"Failed to assign role: {response.text}")
    
    async def get_client_token(self) -> str:
        """Get client credentials token."""
        if not self.client_secret:
            raise KeycloakError("Client secret required for client credentials flow")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
        
        if response.status_code != 200:
            raise KeycloakAuthenticationError(
                f"Failed to get client token: {response.text}"
            )
        
        return response.json()["access_token"]


# Global Keycloak client instance
keycloak_client = KeycloakClient()


class KeycloakAdapter:
    """Adapter pattern for Keycloak integration."""
    
    def __init__(self, client: KeycloakClient):
        self.client = client
    
    async def authenticate_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user info."""
        return await self.client.validate_token(token)
    
    async def authorize_user(self, token: str, required_roles: List[str]) -> bool:
        """Check if user has required roles."""
        user_roles = await self.client.get_user_roles(token)
        return any(role in user_roles for role in required_roles)
    
    async def get_user_permissions(self, token: str) -> List[str]:
        """Get user permissions based on roles."""
        roles = await self.client.get_user_roles(token)
        
        # Map roles to permissions
        permission_mapping = {
            "bank-admin": ["account:read", "account:write", "account:delete", 
                          "transaction:read", "transaction:write", "user:read", "user:write"],
            "account-manager": ["account:read", "account:write", "transaction:read", 
                               "transaction:write", "user:read"],
            "customer": ["account:read", "transaction:read"],
            "support": ["account:read", "transaction:read", "user:read"]
        }
        
        permissions = set()
        for role in roles:
            if role in permission_mapping:
                permissions.update(permission_mapping[role])
        
        return list(permissions)


# Global adapter instance
keycloak_adapter = KeycloakAdapter(keycloak_client)
