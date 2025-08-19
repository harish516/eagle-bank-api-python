"""Error response schemas."""

from typing import List
from pydantic import BaseModel, Field, ConfigDict


class ErrorResponse(BaseModel):
    """Standard error response."""
    message: str = Field(..., description="Error message")
    error_code: str = Field(default="GENERAL_ERROR", description="Machine-readable error code")
    request_id: str = Field(None, description="Request correlation ID for debugging")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "An error occurred",
            "error_code": "GENERAL_ERROR",
            "request_id": "req-abc123def456"
        }
    })


class ValidationError(BaseModel):
    """Validation error detail."""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    type: str = Field(..., description="Type of validation error")
    input_value: str = Field(None, description="The value that failed validation")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "field": "amount",
                "message": "Amount must be greater than 0",
                "type": "value_error",
                "input_value": "-10.50"
            }
        })


class BadRequestErrorResponse(BaseModel):
    """Bad request error response with validation details."""
    message: str = Field(default="Validation error", description="Error message")
    error_code: str = Field(default="VALIDATION_ERROR", description="Machine-readable error code")
    details: List[ValidationError] = Field(..., description="List of validation errors")
    request_id: str = Field(None, description="Request correlation ID for debugging")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "message": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": [
                    {
                        "field": "amount",
                        "message": "Amount must be greater than 0",
                        "type": "value_error",
                        "input_value": "-10.50"
                    },
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "type": "value_error",
                        "input_value": "invalid-email"
                    }
                ],
                "request_id": "req-abc123def456"
            }
        })


class UnauthorizedErrorResponse(BaseModel):
    """Unauthorized error response."""
    message: str = Field(default="Authentication required", description="Error message")
    error_code: str = Field(default="UNAUTHORIZED", description="Machine-readable error code")
    request_id: str = Field(None, description="Request correlation ID for debugging")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "message": "Authentication required",
                "error_code": "UNAUTHORIZED",
                "request_id": "req-abc123def456"
            }
        })


class ForbiddenErrorResponse(BaseModel):
    """Forbidden error response."""
    message: str = Field(default="Insufficient permissions", description="Error message")
    error_code: str = Field(default="FORBIDDEN", description="Machine-readable error code")
    required_permission: str = Field(None, description="Permission required for this action")
    request_id: str = Field(None, description="Request correlation ID for debugging")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "message": "Insufficient permissions",
                "error_code": "FORBIDDEN", 
                "required_permission": "account:write",
                "request_id": "req-abc123def456"
            }
        })


class NotFoundErrorResponse(BaseModel):
    """Not found error response."""
    message: str = Field(default="Resource not found", description="Error message")
    error_code: str = Field(default="NOT_FOUND", description="Machine-readable error code")
    resource_type: str = Field(None, description="Type of resource that was not found")
    resource_id: str = Field(None, description="ID of resource that was not found")
    request_id: str = Field(None, description="Request correlation ID for debugging")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "message": "Bank account was not found",
                "error_code": "ACCOUNT_NOT_FOUND",
                "resource_type": "bank_account",
                "resource_id": "01234567",
                "request_id": "req-abc123def456"
            }
        })
