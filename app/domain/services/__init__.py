"""Domain services implementing business logic."""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import asyncio
import logging

from ..entities import User, Account, Transaction, TransactionType, Currency
from ...core.security import SecurityUtils
from ...core.events import (
    UserCreatedEvent,
    AccountCreatedEvent,
    TransactionCreatedEvent,
    BalanceUpdatedEvent,
)


logger = logging.getLogger(__name__)


class DomainService(ABC):
    """Base class for domain services."""

    def __init__(self, repository):
        self.repository = repository


class UserService(DomainService):
    """User domain service."""

    def create_user(self, user: User) -> User:
        """Create a new user."""
        logger.info(f"Creating user: {user.email}")

        # Check if user already exists
        existing_user = self.repository.get_user_by_email(user.email)
        if existing_user:
            raise ValueError(f"User with email {user.email} already exists")

        # Save user
        created_user = self.repository.create_user(user)

        # Publish domain event
        event = UserCreatedEvent(
            {
                "user_id": created_user.id,
                "email": created_user.email,
                "name": created_user.name,
            }
        )

        logger.info(f"User created successfully: {created_user.id}")
        return created_user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.repository.get_user_by_id(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.repository.get_user_by_email(email)

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> User:
        """Update user."""
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Update user entity
        user.update(**update_data)

        # Save updated user
        return self.repository.update_user(user)

    def delete_user(self, user_id: str) -> None:
        """Delete user."""
        self.repository.delete_user(user_id)

    def user_has_accounts(self, user_id: str) -> bool:
        """Check if user has any accounts."""
        return self.repository.user_has_accounts(user_id)


class AccountService(DomainService):
    """Account domain service."""

    async def create_account(self, account: Account, user_id: str) -> Account:
        """Create a new bank account."""
        logger.info(f"Creating account for user: {user_id}")

        # Set user ID
        account.user_id = user_id

        # Validate user exists
        user_service = UserService(self.repository)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Save account
        created_account = await self.repository.create_account(account)

        # Publish domain event
        event = AccountCreatedEvent(
            {
                "account_number": created_account.account_number,
                "user_id": user_id,
                "account_type": created_account.account_type.value,
            }
        )

        logger.info(f"Account created successfully: {created_account.account_number}")
        return created_account

    async def get_account_by_number(self, account_number: str) -> Optional[Account]:
        """Get account by account number."""
        return await self.repository.get_account_by_number(account_number)

    async def get_accounts_by_user(self, user_id: str) -> List[Account]:
        """Get all accounts for a user."""
        return await self.repository.get_accounts_by_user(user_id)

    async def update_account(
        self, account_number: str, update_data: Dict[str, Any]
    ) -> Account:
        """Update account."""
        account = await self.repository.get_account_by_number(account_number)
        if not account:
            raise ValueError(f"Account {account_number} not found")

        # Update account entity
        account.update(**update_data)

        # Save updated account
        return await self.repository.update_account(account)

    async def delete_account(self, account_number: str) -> None:
        """Delete account."""
        account = await self.repository.get_account_by_number(account_number)
        if not account:
            raise ValueError(f"Account {account_number} not found")

        if account.balance > 0:
            raise ValueError("Cannot delete account with positive balance")

        await self.repository.delete_account(account_number)

    async def check_account_ownership(self, account_number: str, user_id: str) -> bool:
        """Check if user owns the account."""
        account = await self.repository.get_account_by_number(account_number)
        return account and account.user_id == user_id


class TransactionService(DomainService):
    """Transaction domain service with async/await and concurrency patterns."""

    def __init__(self, repository, account_service: AccountService = None):
        super().__init__(repository)
        self.account_service = account_service or AccountService(repository)

    async def create_transaction(
        self, transaction: Transaction, user_id: str
    ) -> Transaction:
        """Create a new transaction with account balance update."""
        logger.info(f"Creating {transaction.type} transaction: {transaction.amount}")

        # Set user ID
        transaction.user_id = user_id

        # Get account and validate ownership
        account = await self.account_service.get_account_by_number(
            transaction.account_number
        )
        if not account:
            raise ValueError(f"Account {transaction.account_number} not found")

        if not await self.account_service.check_account_ownership(
            transaction.account_number, user_id
        ):
            raise ValueError("User does not own this account")

        # Validate transaction
        if transaction.type == TransactionType.WITHDRAWAL:
            if not account.can_withdraw(transaction.amount):
                raise ValueError("Insufficient funds to process transaction")

        # Use concurrency for transaction processing
        try:
            # Process transaction and update balance concurrently
            transaction_task = asyncio.create_task(self._save_transaction(transaction))
            balance_task = asyncio.create_task(
                self._update_account_balance(account, transaction)
            )

            # Wait for both operations to complete
            saved_transaction, (old_balance, new_balance) = await asyncio.gather(
                transaction_task, balance_task
            )

            # Publish events asynchronously
            await asyncio.gather(
                self._publish_transaction_event(saved_transaction),
                self._publish_balance_event(
                    account.account_number, old_balance, new_balance
                ),
            )

            logger.info(f"Transaction completed: {saved_transaction.id}")
            return saved_transaction

        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise

    async def _save_transaction(self, transaction: Transaction) -> Transaction:
        """Save transaction to repository."""
        return await self.repository.create_transaction(transaction)

    async def _update_account_balance(
        self, account: Account, transaction: Transaction
    ) -> tuple[float, float]:
        """Update account balance based on transaction."""
        if transaction.type == TransactionType.DEPOSIT:
            old_balance, new_balance = account.deposit(transaction.amount)
        else:  # WITHDRAWAL
            old_balance, new_balance = account.withdraw(transaction.amount)

        # Save updated account
        await self.repository.update_account(account)

        return old_balance, new_balance

    async def _publish_transaction_event(self, transaction: Transaction):
        """Publish transaction created event."""
        event = TransactionCreatedEvent(
            {
                "transaction_id": transaction.id,
                "account_number": transaction.account_number,
                "amount": transaction.amount,
                "type": transaction.type.value,
                "user_id": transaction.user_id,
            }
        )

    async def _publish_balance_event(
        self, account_number: str, old_balance: float, new_balance: float
    ):
        """Publish balance updated event."""
        event = BalanceUpdatedEvent(account_number, old_balance, new_balance)

    async def get_transaction_by_id(
        self, account_number: str, transaction_id: str
    ) -> Optional[Transaction]:
        """Get transaction by ID."""
        return await self.repository.get_transaction_by_id(
            account_number, transaction_id
        )

    async def get_transactions_by_account(
        self, account_number: str, limit: int = 100, offset: int = 0
    ) -> List[Transaction]:
        """Get transactions for an account."""
        return await self.repository.get_transactions_by_account(
            account_number, limit, offset
        )

    async def get_account_balance_async(self, account_number: str) -> float:
        """Get account balance asynchronously."""
        account = await self.account_service.get_account_by_number(account_number)
        if not account:
            raise ValueError(f"Account {account_number} not found")

        return account.balance


class NotificationService:
    """Service for handling notifications (event-driven)."""

    def __init__(self):
        self.subscribers = []

    async def notify_account_created(self, event_data: Dict[str, Any]):
        """Handle account created event."""
        logger.info(
            f"Sending account creation notification for: {event_data['account_number']}"
        )

        # Simulate external notification service call
        await asyncio.sleep(0.1)

        # In real implementation, send email/SMS/push notification
        logger.info("Account creation notification sent")

    async def notify_transaction_created(self, event_data: Dict[str, Any]):
        """Handle transaction created event."""
        logger.info(
            f"Sending transaction notification for: {event_data['transaction_id']}"
        )

        # Simulate external notification service call
        await asyncio.sleep(0.1)

        # In real implementation, send transaction notification
        logger.info("Transaction notification sent")

    async def notify_balance_updated(self, event_data: Dict[str, Any]):
        """Handle balance updated event."""
        logger.info(f"Balance updated for account: {event_data['account_number']}")

        # In real implementation, update real-time dashboard, send alerts, etc.
        logger.info("Balance update notification processed")
