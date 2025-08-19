"""Common base models and enums for all schemas."""

from enum import Enum
from pydantic import BaseModel, ConfigDict


class AccountType(str, Enum):
    """Account type enumeration."""
    PERSONAL = "personal"
    BUSINESS = "business"
    SAVINGS = "savings"


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class Currency(str, Enum):
    """Currency enumeration."""
    GBP = "GBP"
    USD = "USD"
    EUR = "EUR"


class BaseResponseModel(BaseModel):
    """Base response model with common configuration."""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
