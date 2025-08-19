"""Transaction-related schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
import re

from .base import BaseResponseModel, TransactionType, Currency


class CreateTransactionRequest(BaseModel):
    """Request model for creating a transaction."""
    amount: float = Field(..., gt=0.0, le=10000000.0,
                         description="Transaction amount")
    currency: Currency = Field(default=Currency.GBP)
    type: TransactionType
    reference: Optional[str] = Field(None, max_length=100, description="Transaction reference")
    
    @field_validator('amount', mode='before')
    @classmethod
    def validate_amount(cls, v):
        """Validate amount has at most 2 decimal places and is positive."""
        if v is None:
            raise ValueError('Amount is required')
        
        try:
            amount_float = float(v)
        except (ValueError, TypeError):
            raise ValueError('Amount must be a valid number')
        
        if amount_float <= 0:
            raise ValueError('Amount must be greater than 0')
        
        if amount_float > 10000000:
            raise ValueError('Amount cannot exceed £10,000,000')
        
        # Check for at most 2 decimal places
        if round(amount_float, 2) != amount_float:
            raise ValueError('Amount must have at most 2 decimal places')
        
        return amount_float
    
    @field_validator('reference', mode='before')
    @classmethod
    def validate_reference(cls, v):
        """Validate transaction reference."""
        if v is None:
            return v
        
        ref_str = str(v).strip()
        if len(ref_str) == 0:
            return None
        
        # Reference should contain alphanumeric characters, spaces, and common punctuation
        pattern = r"^[a-zA-Z0-9\s\-_.,;:()\[\]{}/'\"!@#$%&*+=|\\~`]+$"
        if not re.match(pattern, ref_str):
            raise ValueError('Reference contains invalid characters')
        
        return ref_str
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "amount": 100.50,
            "currency": "GBP",
            "type": "deposit",
            "reference": "Salary payment"
        }
    })


class TransactionResponse(BaseResponseModel):
    """Response model for transaction data."""
    id: str = Field(..., description="Unique transaction identifier")
    amount: float = Field(..., ge=0.0)
    currency: Currency
    type: TransactionType
    reference: Optional[str] = None
    user_id: Optional[str] = Field(None, description="User who initiated the transaction")
    account_number: Optional[str] = Field(None, description="Associated account number")
    balance_after: Optional[float] = Field(None, description="Account balance after transaction")
    created_timestamp: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_transaction_id(cls, v):
        """Validate transaction ID format."""
        if not v:
            raise ValueError('Transaction ID is required')
        
        # Transaction ID should follow pattern: tan-{alphanumeric}
        pattern = r'^tan-[A-Za-z0-9]+$'
        if not re.match(pattern, str(v)):
            raise ValueError('Invalid transaction ID format')
        
        return str(v)
    
    @field_validator('user_id', mode='before')
    @classmethod
    def validate_user_id(cls, v):
        """Validate user ID format."""
        if v is None:
            return v
        
        # User ID should follow pattern: usr-{alphanumeric}
        pattern = r'^usr-[A-Za-z0-9]+$'
        if not re.match(pattern, str(v)):
            raise ValueError('Invalid user ID format')
        
        return str(v)
    
    @field_validator('account_number', mode='before')
    @classmethod
    def validate_account_number(cls, v):
        """Validate account number format."""
        if v is None:
            return v
        
        # Account number should be 8 digits starting with 01
        pattern = r'^01\d{6}$'
        if not re.match(pattern, str(v)):
            raise ValueError('Invalid account number format')
        
        return str(v)
    
    @field_validator('balance_after', mode='before')
    @classmethod
    def validate_balance_after(cls, v):
        """Validate balance after transaction."""
        if v is None:
            return v
        
        try:
            balance_float = float(v)
        except (ValueError, TypeError):
            raise ValueError('Balance after must be a valid number')
        
        # Check for at most 2 decimal places
        if round(balance_float, 2) != balance_float:
            raise ValueError('Balance after must have at most 2 decimal places')
        
        return balance_float
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "tan-123abc456def",
            "amount": 100.50,
            "currency": "GBP",
            "type": "deposit",
            "reference": "Salary payment",
            "user_id": "usr-abc123def456",
            "account_number": "01234567",
            "balance_after": 1100.50,
            "created_timestamp": "2024-01-01T10:00:00Z"
        }
    })


class ListTransactionsResponse(BaseModel):
    """Response model for listing transactions."""
    transactions: List[TransactionResponse]
    total_count: int = Field(..., description="Total number of transactions")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Number of transactions per page")
    
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
    
    @field_validator('page', mode='before')
    @classmethod
    def validate_page(cls, v):
        """Validate page number is positive."""
        try:
            page_num = int(v)
        except (ValueError, TypeError):
            raise ValueError('Page must be a valid integer')
        
        if page_num < 1:
            raise ValueError('Page must be 1 or greater')
        
        return page_num
    
    @field_validator('page_size', mode='before')
    @classmethod
    def validate_page_size(cls, v):
        """Validate page size is within reasonable limits."""
        try:
            size = int(v)
        except (ValueError, TypeError):
            raise ValueError('Page size must be a valid integer')
        
        if size < 1:
            raise ValueError('Page size must be 1 or greater')
        
        if size > 1000:
            raise ValueError('Page size cannot exceed 1000')
        
        return size
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "transactions": [
                {
                    "id": "tan-123abc456def",
                    "amount": 100.50,
                    "currency": "GBP",
                    "type": "deposit",
                    "reference": "Salary payment",
                    "user_id": "usr-abc123def456",
                    "account_number": "01234567",
                    "balance_after": 1100.50,
                    "created_timestamp": "2024-01-01T10:00:00Z"
                }
            ],
            "total_count": 1,
            "page": 1,
            "page_size": 50
        }
    })
