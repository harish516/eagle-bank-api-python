"""Schemas package with modular organization."""

# Base models and enums
from .base import (
    AccountType,
    TransactionType,
    Currency,
    BaseResponseModel
)

# Address schemas
from .address import AddressBase

# User schemas
from .users import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse
)

# Account schemas  
from .accounts import (
    CreateBankAccountRequest,
    UpdateBankAccountRequest,
    BankAccountResponse,
    ListBankAccountsResponse
)

# Transaction schemas
from .transactions import (
    CreateTransactionRequest,
    TransactionResponse,
    ListTransactionsResponse
)

# Error schemas
from .errors import (
    ErrorResponse,
    ValidationError,
    BadRequestErrorResponse,
    UnauthorizedErrorResponse,
    ForbiddenErrorResponse,
    NotFoundErrorResponse
)

__all__ = [
    # Base
    "AccountType",
    "TransactionType", 
    "Currency",
    "BaseResponseModel",
    
    # Address
    "AddressBase",
    
    # Users
    "CreateUserRequest",
    "UpdateUserRequest", 
    "UserResponse",
    
    # Accounts
    "CreateBankAccountRequest",
    "UpdateBankAccountRequest",
    "BankAccountResponse",
    "ListBankAccountsResponse",
    
    # Transactions
    "CreateTransactionRequest",
    "TransactionResponse",
    "ListTransactionsResponse",
    
    # Errors
    "ErrorResponse",
    "ValidationError",
    "BadRequestErrorResponse",
    "UnauthorizedErrorResponse",
    "ForbiddenErrorResponse", 
    "NotFoundErrorResponse"
]
