"""User-related schemas."""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import datetime
import re

from .base import BaseResponseModel
from .address import AddressBase


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""
    name: str = Field(..., min_length=1, max_length=100)
    address: AddressBase
    phone_number: str = Field(..., description="International phone number with country code")
    email: EmailStr
    
    @field_validator('phone_number', mode='before')
    @classmethod
    def validate_phone_number(cls, v):
        """Validate international phone number format."""
        if not v:
            raise ValueError('Phone number is required')
        
        # International phone number validation (E.164 format)
        pattern = r'^\+[1-9]\d{1,14}$'
        phone_str = str(v).strip()
        
        if not re.match(pattern, phone_str):
            raise ValueError('Phone number must be in international format (e.g., +447700900123)')
        
        return phone_str
    
    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, v):
        """Validate name contains only letters, spaces, hyphens, and apostrophes."""
        if not v:
            raise ValueError('Name is required')
        
        name_str = str(v).strip()
        if len(name_str) < 1:
            raise ValueError('Name cannot be empty')
        
        # Allow letters, spaces, hyphens, apostrophes, and periods
        pattern = r"^[a-zA-Z\s\-'.]+$"
        if not re.match(pattern, name_str):
            raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
        
        return name_str
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "John Doe",
            "address": {
                "line1": "123 Main Street",
                "line2": "Apt 4B",
                "town": "London",
                "county": "Greater London",
                "postcode": "SW1A 1AA"
            },
            "phone_number": "+447700900123",
            "email": "john.doe@example.com"
        }
    })


class UpdateUserRequest(BaseModel):
    """Request model for updating a user."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[AddressBase] = None
    phone_number: Optional[str] = Field(None, description="International phone number with country code")
    email: Optional[EmailStr] = None
    
    @field_validator('phone_number', mode='before')
    @classmethod
    def validate_phone_number(cls, v):
        """Validate international phone number format."""
        if v is None:
            return v
        
        # International phone number validation (E.164 format)
        pattern = r'^\+[1-9]\d{1,14}$'
        phone_str = str(v).strip()
        
        if not re.match(pattern, phone_str):
            raise ValueError('Phone number must be in international format (e.g., +447700900123)')
        
        return phone_str
    
    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, v):
        """Validate name contains only letters, spaces, hyphens, and apostrophes."""
        if v is None:
            return v
        
        name_str = str(v).strip()
        if len(name_str) < 1:
            raise ValueError('Name cannot be empty')
        
        # Allow letters, spaces, hyphens, apostrophes, and periods
        pattern = r"^[a-zA-Z\s\-'.]+$"
        if not re.match(pattern, name_str):
            raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
        
        return name_str


class UserResponse(BaseResponseModel):
    """Response model for user data."""
    id: str = Field(..., description="Unique user identifier")
    name: str
    address: AddressBase
    phone_number: str
    email: str
    created_timestamp: datetime
    updated_timestamp: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_user_id(cls, v):
        """Validate user ID format."""
        if not v:
            raise ValueError('User ID is required')
        
        # User ID should follow pattern: usr-{alphanumeric}
        pattern = r'^usr-[A-Za-z0-9]+$'
        if not re.match(pattern, str(v)):
            raise ValueError('Invalid user ID format')
        
        return str(v)
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "usr-abc123def456",
            "name": "John Doe",
            "address": {
                "line1": "123 Main Street",
                "line2": "Apt 4B",
                "town": "London",
                "county": "Greater London",
                "postcode": "SW1A 1AA"
            },
            "phone_number": "+447700900123",
            "email": "john.doe@example.com",
            "created_timestamp": "2024-01-01T10:00:00Z",
            "updated_timestamp": "2024-01-01T10:00:00Z"
        }
    })