"""Account-related schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
import re

from .base import BaseResponseModel, AccountType, Currency


class CreateBankAccountRequest(BaseModel):
    """Request model for creating a bank account."""
    name: str = Field(..., min_length=1, max_length=100, 
                     description="Account name", 
                     example="Personal Bank Account")
    account_type: AccountType = Field(..., description="Account type")
    
    @field_validator('name', mode='before')
    @classmethod
    def validate_account_name(cls, v):
        """Validate account name."""
        if not v:
            raise ValueError('Account name is required')
        
        name_str = str(v).strip()
        if len(name_str) < 1:
            raise ValueError('Account name cannot be empty')
        
        # Account name should be alphanumeric with spaces, hyphens, and apostrophes
        pattern = r"^[a-zA-Z0-9\s\-'.]+$"
        if not re.match(pattern, name_str):
            raise ValueError('Account name can only contain letters, numbers, spaces, hyphens, apostrophes, and periods')
        
        return name_str
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Personal Bank Account",
            "account_type": "personal"
        }
    })


class UpdateBankAccountRequest(BaseModel):
    """Request model for updating a bank account."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    account_type: Optional[AccountType] = None
    
    @field_validator('name', mode='before')
    @classmethod
    def validate_account_name(cls, v):
        """Validate account name."""
        if v is None:
            return v
        
        name_str = str(v).strip()
        if len(name_str) < 1:
            raise ValueError('Account name cannot be empty')
        
        # Account name should be alphanumeric with spaces, hyphens, and apostrophes
        pattern = r"^[a-zA-Z0-9\s\-'.]+$"
        if not re.match(pattern, name_str):
            raise ValueError('Account name can only contain letters, numbers, spaces, hyphens, apostrophes, and periods')
        
        return name_str


class BankAccountResponse(BaseResponseModel):
    """Response model for bank account data."""
    account_number: str = Field(..., description="8-digit account number")
    sort_code: str = Field(..., example="10-10-10", description="Bank sort code")
    name: str
    account_type: AccountType
    balance: float = Field(..., ge=0.0, le=10000000.0, 
                          description="Account balance")
    currency: Currency
    created_timestamp: datetime
    updated_timestamp: datetime
    
    @field_validator('account_number', mode='before')
    @classmethod
    def validate_account_number(cls, v):
        """Validate account number format."""
        if not v:
            raise ValueError('Account number is required')
        
        # Account number should be 8 digits starting with 01
        pattern = r'^01\d{6}$'
        account_str = str(v).strip()
        
        if not re.match(pattern, account_str):
            raise ValueError('Account number must be 8 digits starting with 01 (e.g., 01234567)')
        
        return account_str
    
    @field_validator('sort_code', mode='before')
    @classmethod
    def validate_sort_code(cls, v):
        """Validate sort code format."""
        if not v:
            raise ValueError('Sort code is required')
        
        # Sort code should be in format XX-XX-XX
        pattern = r'^\d{2}-\d{2}-\d{2}$'
        sort_code_str = str(v).strip()
        
        if not re.match(pattern, sort_code_str):
            raise ValueError('Sort code must be in format XX-XX-XX (e.g., 10-10-10)')
        
        return sort_code_str
    
    @field_validator('balance', mode='before')
    @classmethod
    def validate_balance(cls, v):
        """Validate balance has at most 2 decimal places."""
        if v is None:
            return 0.0
        
        try:
            balance_float = float(v)
        except (ValueError, TypeError):
            raise ValueError('Balance must be a valid number')
        
        if balance_float < 0:
            raise ValueError('Balance cannot be negative')
        
        # Check for at most 2 decimal places
        if round(balance_float, 2) != balance_float:
            raise ValueError('Balance must have at most 2 decimal places')
        
        return balance_float
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "account_number": "01234567",
            "sort_code": "10-10-10",
            "name": "Personal Bank Account",
            "account_type": "personal",
            "balance": 1000.00,
            "currency": "GBP",
            "created_timestamp": "2024-01-01T10:00:00Z",
            "updated_timestamp": "2024-01-01T10:00:00Z"
        }
    })


class ListBankAccountsResponse(BaseModel):
    """Response model for listing bank accounts."""
    accounts: List[BankAccountResponse]
    total_count: int = Field(..., description="Total number of accounts")
    
    @field_validator('total_count', mode='before')
    @classmethod
    def validate_total_count(cls, v):
        """Validate total count is non-negative."""
        try:
            count = int(v)
        except (ValueError, TypeError):
            raise ValueError('Total count must be a valid integer')
        
        if count < 0:
            raise ValueError('Total count cannot be negative')
        
        return count
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "accounts": [
                {
                    "account_number": "01234567",
                    "sort_code": "10-10-10",
                    "name": "Personal Bank Account",
                    "account_type": "personal",
                    "balance": 1000.00,
                    "currency": "GBP",
                    "created_timestamp": "2024-01-01T10:00:00Z",
                    "updated_timestamp": "2024-01-01T10:00:00Z"
                }
            ],
            "total_count": 1
        }
    })
