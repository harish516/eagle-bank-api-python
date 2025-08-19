"""Repository pattern implementations for data access."""

from typing import List, Optional
from abc import ABC
from sqlalchemy.orm import Session

from ..database.models import UserModel, AccountModel, TransactionModel
from ...domain.entities import User, Account, Transaction


class Repository(ABC):
    """Abstract repository base class."""

    def __init__(self, db: Session):
        self.db = db


class UserRepository(Repository):
    """User repository implementation."""

    def create_user(self, user: User) -> User:
        """Create a new user."""
        db_user = UserModel(
            id=user.id,
            name=user.name,
            address=user.address,
            phone_number=user.phone_number,
            email=user.email,
            created_timestamp=user.created_timestamp,
            updated_timestamp=user.updated_timestamp,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return self._model_to_entity(db_user)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._model_to_entity(db_user) if db_user else None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._model_to_entity(db_user) if db_user else None

    def update_user(self, user: User) -> User:
        """Update user."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not db_user:
            raise ValueError(f"User {user.id} not found")

        db_user.name = user.name
        db_user.address = user.address
        db_user.phone_number = user.phone_number
        db_user.email = user.email
        db_user.updated_timestamp = user.updated_timestamp

        self.db.commit()
        self.db.refresh(db_user)

        return self._model_to_entity(db_user)

    def delete_user(self, user_id: str) -> None:
        """Delete user."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if db_user:
            self.db.delete(db_user)
            self.db.commit()

    def user_has_accounts(self, user_id: str) -> bool:
        """Check if user has any accounts."""
        count = (
            self.db.query(AccountModel).filter(AccountModel.user_id == user_id).count()
        )
        return count > 0

    def _model_to_entity(self, db_user: UserModel) -> User:
        """Convert database model to domain entity."""
        return User(
            id=db_user.id,
            name=db_user.name,
            address=db_user.address,
            phone_number=db_user.phone_number,
            email=db_user.email,
            created_timestamp=db_user.created_timestamp,
            updated_timestamp=db_user.updated_timestamp,
        )


class AccountRepository(Repository):
    """Account repository implementation."""

    async def create_account(self, account: Account) -> Account:
        """Create a new account."""
        db_account = AccountModel(
            account_number=account.account_number,
            sort_code=account.sort_code,
            name=account.name,
            account_type=account.account_type.value,
            balance=account.balance,
            currency=account.currency.value,
            user_id=account.user_id,
            created_timestamp=account.created_timestamp,
            updated_timestamp=account.updated_timestamp,
        )

        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)

        return self._model_to_entity(db_account)

    async def get_account_by_number(self, account_number: str) -> Optional[Account]:
        """Get account by account number."""
        db_account = (
            self.db.query(AccountModel)
            .filter(AccountModel.account_number == account_number)
            .first()
        )
        return self._model_to_entity(db_account) if db_account else None

    async def get_accounts_by_user(self, user_id: str) -> List[Account]:
        """Get all accounts for a user."""
        db_accounts = (
            self.db.query(AccountModel).filter(AccountModel.user_id == user_id).all()
        )
        return [self._model_to_entity(acc) for acc in db_accounts]

    async def update_account(self, account: Account) -> Account:
        """Update account."""
        db_account = (
            self.db.query(AccountModel)
            .filter(AccountModel.account_number == account.account_number)
            .first()
        )
        if not db_account:
            raise ValueError(f"Account {account.account_number} not found")

        db_account.name = account.name
        db_account.account_type = account.account_type.value
        db_account.balance = account.balance
        db_account.updated_timestamp = account.updated_timestamp

        self.db.commit()
        self.db.refresh(db_account)

        return self._model_to_entity(db_account)

    async def delete_account(self, account_number: str) -> None:
        """Delete account."""
        db_account = (
            self.db.query(AccountModel)
            .filter(AccountModel.account_number == account_number)
            .first()
        )
        if db_account:
            self.db.delete(db_account)
            self.db.commit()

    def _model_to_entity(self, db_account: AccountModel) -> Account:
        """Convert database model to domain entity."""
        from ...domain.entities import AccountType, Currency

        return Account(
            account_number=db_account.account_number,
            sort_code=db_account.sort_code,
            name=db_account.name,
            account_type=AccountType(db_account.account_type),
            balance=db_account.balance,
            currency=Currency(db_account.currency),
            user_id=db_account.user_id,
            created_timestamp=db_account.created_timestamp,
            updated_timestamp=db_account.updated_timestamp,
        )


class TransactionRepository(Repository):
    """Transaction repository implementation."""

    async def create_transaction(self, transaction: Transaction) -> Transaction:
        """Create a new transaction."""
        db_transaction = TransactionModel(
            id=transaction.id,
            account_number=transaction.account_number,
            amount=transaction.amount,
            currency=transaction.currency.value,
            type=transaction.type.value,
            reference=transaction.reference,
            user_id=transaction.user_id,
            created_timestamp=transaction.created_timestamp,
        )

        self.db.add(db_transaction)
        self.db.commit()
        self.db.refresh(db_transaction)

        return self._model_to_entity(db_transaction)

    async def get_transaction_by_id(
        self, account_number: str, transaction_id: str
    ) -> Optional[Transaction]:
        """Get transaction by ID."""
        db_transaction = (
            self.db.query(TransactionModel)
            .filter(
                TransactionModel.id == transaction_id,
                TransactionModel.account_number == account_number,
            )
            .first()
        )
        return self._model_to_entity(db_transaction) if db_transaction else None

    async def get_transactions_by_account(
        self, account_number: str, limit: int = 100, offset: int = 0
    ) -> List[Transaction]:
        """Get transactions for an account."""
        db_transactions = (
            self.db.query(TransactionModel)
            .filter(TransactionModel.account_number == account_number)
            .order_by(TransactionModel.created_timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [self._model_to_entity(tx) for tx in db_transactions]

    def _model_to_entity(self, db_transaction: TransactionModel) -> Transaction:
        """Convert database model to domain entity."""
        from ...domain.entities import TransactionType, Currency

        return Transaction(
            id=db_transaction.id,
            account_number=db_transaction.account_number,
            amount=db_transaction.amount,
            currency=Currency(db_transaction.currency),
            type=TransactionType(db_transaction.type),
            reference=db_transaction.reference,
            user_id=db_transaction.user_id,
            created_timestamp=db_transaction.created_timestamp,
        )


class UnitOfWork:
    """Unit of Work pattern implementation."""

    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.accounts = AccountRepository(db)
        self.transactions = TransactionRepository(db)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        else:
            self.db.commit()
        self.db.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        else:
            self.db.commit()
        self.db.close()
