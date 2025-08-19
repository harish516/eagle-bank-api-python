"""SQLAlchemy database models."""

from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class UserModel(Base):
    """User database model."""
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(JSON, nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    created_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_timestamp = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    accounts = relationship("AccountModel", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("TransactionModel", back_populates="user")


class AccountModel(Base):
    """Account database model."""
    __tablename__ = "accounts"
    
    account_number = Column(String(8), primary_key=True, index=True)
    sort_code = Column(String(8), nullable=False, default="10-10-10")
    name = Column(String(100), nullable=False)
    account_type = Column(String(20), nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), nullable=False, default="GBP")
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    created_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_timestamp = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("UserModel", back_populates="accounts")
    transactions = relationship("TransactionModel", back_populates="account", cascade="all, delete-orphan")


class TransactionModel(Base):
    """Transaction database model."""
    __tablename__ = "transactions"
    
    id = Column(String(50), primary_key=True, index=True)
    account_number = Column(String(8), ForeignKey("accounts.account_number"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    type = Column(String(20), nullable=False)
    reference = Column(String(100), nullable=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    created_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    account = relationship("AccountModel", back_populates="transactions")
    user = relationship("UserModel", back_populates="transactions")


class AuditLogModel(Base):
    """Audit log database model."""
    __tablename__ = "audit_logs"
    
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
