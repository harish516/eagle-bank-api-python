"""Domain entities representing core business objects."""

from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class AccountType(str, Enum):
    """Account type enumeration."""
    PERSONAL = "personal"


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class Currency(str, Enum):
    """Currency enumeration."""
    GBP = "GBP"


@dataclass
class User:
    """User domain entity."""
    id: str
    name: str
    address: Dict[str, Any]
    phone_number: str
    email: str
    created_timestamp: datetime = field(default_factory=datetime.utcnow)
    updated_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def update(self, **kwargs):
        """Update user attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        
        self.updated_timestamp = datetime.utcnow()


@dataclass
class Account:
    """Bank account domain entity."""
    account_number: str
    sort_code: str = "10-10-10"
    name: str = ""
    account_type: AccountType = AccountType.PERSONAL
    balance: float = 0.0
    currency: Currency = Currency.GBP
    user_id: Optional[str] = None
    created_timestamp: datetime = field(default_factory=datetime.utcnow)
    updated_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def update(self, **kwargs):
        """Update account attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        
        self.updated_timestamp = datetime.utcnow()
    
    def can_withdraw(self, amount: float) -> bool:
        """Check if withdrawal is possible."""
        return self.balance >= amount
    
    def deposit(self, amount: float):
        """Deposit money to account."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        old_balance = self.balance
        self.balance += amount
        self.updated_timestamp = datetime.utcnow()
        
        return old_balance, self.balance
    
    def withdraw(self, amount: float):
        """Withdraw money from account."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        if not self.can_withdraw(amount):
            raise ValueError("Insufficient funds")
        
        old_balance = self.balance
        self.balance -= amount
        self.updated_timestamp = datetime.utcnow()
        
        return old_balance, self.balance


@dataclass
class Transaction:
    """Transaction domain entity."""
    id: str
    account_number: str
    amount: float
    currency: Currency
    type: TransactionType
    reference: Optional[str] = None
    user_id: Optional[str] = None
    created_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate transaction after initialization."""
        if self.amount <= 0:
            raise ValueError("Transaction amount must be positive")
        
        if self.amount > 10000.0:
            raise ValueError("Transaction amount cannot exceed 10,000")


@dataclass
class AuditLog:
    """Audit log domain entity."""
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
