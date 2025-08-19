"""Transactions API endpoints with async/await and concurrency patterns."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.schemas import (
    CreateTransactionRequest,
    TransactionResponse,
    ListTransactionsResponse,
    ErrorResponse,
    BadRequestErrorResponse,
    UnauthorizedErrorResponse,
    ForbiddenErrorResponse,
    NotFoundErrorResponse
)
from app.auth import (
    require_authentication,
    require_permissions,
    authenticated_user,
    get_current_user
)
from app.domain.services import TransactionService, AccountService, NotificationService
from app.domain.entities import Transaction, TransactionType
from app.api.dependencies import get_db
from app.core.security import SecurityUtils, audit_log, rate_limit
from app.core.events import Event


logger = logging.getLogger(__name__)
router = APIRouter()


class TransactionAdapter:
    """Adapter pattern for external transaction processing systems."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_external_validation(self, transaction: Transaction) -> bool:
        """Simulate external transaction validation (e.g., fraud detection)."""
        logger.info(f"Processing external validation for transaction: {transaction.id}")
        
        # Simulate async external call
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self._validate_transaction_sync,
            transaction
        )
        
        return result
    
    def _validate_transaction_sync(self, transaction: Transaction) -> bool:
        """Synchronous validation logic (simulated)."""
        import time
        time.sleep(0.1)  # Simulate network delay
        
        # Simple validation rules
        if transaction.amount > 5000:
            logger.warning(f"Large transaction detected: {transaction.amount}")
            # In real system, might trigger additional checks
        
        return True  # All transactions pass for demo


class TransactionIterator:
    """Iterator pattern for processing multiple transactions."""
    
    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.index = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.index >= len(self.transactions):
            raise StopIteration
        
        transaction = self.transactions[self.index]
        self.index += 1
        return transaction
    
    async def process_batch_async(self):
        """Process transactions concurrently."""
        tasks = []
        for transaction in self.transactions:
            task = asyncio.create_task(self._process_single_transaction(transaction))
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_transaction(self, transaction: Transaction):
        """Process a single transaction."""
        # Simulate processing
        await asyncio.sleep(0.05)
        return f"Processed: {transaction.id}"


# Global transaction adapter
transaction_adapter = TransactionAdapter()


@router.post(
    "/{account_number}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": BadRequestErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Create a transaction",
    description="Create a new transaction (deposit or withdrawal) for the specified account"
)
@require_authentication
@require_permissions(["transaction:write"])
@rate_limit(calls_per_minute=30)  # Rate limit transactions
@audit_log("create_transaction")
async def create_transaction(
    request: Request,
    account_number: str,
    transaction_data: CreateTransactionRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(authenticated_user),
    db=Depends(get_db)
):
    """Create a new transaction with async processing."""
    try:
        # Validate account number format
        if not SecurityUtils.validate_account_number(account_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account number format"
            )
        
        user_id = current_user.get('sub')
        
        # Create services
        account_service = AccountService(db)
        transaction_service = TransactionService(db, account_service)
        
        # Verify account exists and user ownership
        account = await account_service.get_account_by_number(account_number)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account was not found"
            )
        
        if not await account_service.check_account_ownership(account_number, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user is not allowed to access this account"
            )
        
        # Generate transaction ID
        transaction_id = SecurityUtils.generate_transaction_id()
        
        # Create transaction entity
        transaction = Transaction(
            id=transaction_id,
            account_number=account_number,
            amount=transaction_data.amount,
            currency=transaction_data.currency,
            type=transaction_data.type,
            reference=transaction_data.reference,
            user_id=user_id
        )
        
        # External validation using adapter pattern
        validation_task = asyncio.create_task(
            transaction_adapter.process_external_validation(transaction)
        )
        
        # Create transaction (this handles balance updates internally)
        transaction_task = asyncio.create_task(
            transaction_service.create_transaction(transaction, user_id)
        )
        
        # Wait for both validation and creation concurrently
        validation_result, created_transaction = await asyncio.gather(
            validation_task,
            transaction_task
        )
        
        if not validation_result:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Transaction failed external validation"
            )
        
        # Add background task for notifications
        notification_service = NotificationService()
        background_tasks.add_task(
            notification_service.notify_transaction_created,
            {
                "transaction_id": created_transaction.id,
                "account_number": account_number,
                "amount": created_transaction.amount,
                "type": created_transaction.type.value
            }
        )
        
        # Publish event
        if hasattr(request.app, 'publish_event'):
            await request.app.publish_event(
                "transaction.created",
                {
                    "transaction_id": created_transaction.id,
                    "account_number": account_number,
                    "amount": created_transaction.amount,
                    "type": created_transaction.type.value,
                    "user_id": user_id
                }
            )
        
        logger.info(f"Transaction created: {created_transaction.id}")
        
        return TransactionResponse.from_orm(created_transaction)
        
    except HTTPException:
        raise
    except ValueError as e:
        if "Insufficient funds" in str(e):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Insufficient funds to process transaction"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Transaction creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/{account_number}/transactions",
    response_model=ListTransactionsResponse,
    responses={
        400: {"model": BadRequestErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="List transactions",
    description="List all transactions for the specified account"
)
@require_authentication
@require_permissions(["transaction:read"])
async def list_account_transactions(
    request: Request,
    account_number: str,
    limit: int = 100,
    offset: int = 0,
    current_user=Depends(authenticated_user),
    db=Depends(get_db)
):
    """List transactions for an account with async processing."""
    try:
        # Validate account number format
        if not SecurityUtils.validate_account_number(account_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account number format"
            )
        
        user_id = current_user.get('sub')
        
        # Create services
        account_service = AccountService(db)
        transaction_service = TransactionService(db, account_service)
        
        # Verify account exists and user ownership
        account = await account_service.get_account_by_number(account_number)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account was not found"
            )
        
        # Check ownership
        user_permissions = getattr(request.state, 'permissions', [])
        if (account.user_id != user_id and 
            not any(perm in user_permissions for perm in ['admin', 'transaction:read:all'])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user is not allowed to access the transactions"
            )
        
        # Get transactions asynchronously
        transactions = await transaction_service.get_transactions_by_account(
            account_number, limit, offset
        )
        
        # Convert to response models using iterator pattern
        transaction_iterator = TransactionIterator(transactions)
        transaction_responses = []
        
        for transaction in transaction_iterator:
            transaction_responses.append(TransactionResponse.from_orm(transaction))
        
        return ListTransactionsResponse(transactions=transaction_responses)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list transactions for account {account_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/{account_number}/transactions/{transaction_id}",
    response_model=TransactionResponse,
    responses={
        400: {"model": BadRequestErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Fetch transaction by ID",
    description="Retrieve transaction details by transaction ID"
)
@require_authentication
@require_permissions(["transaction:read"])
@audit_log("fetch_transaction")
async def fetch_account_transaction_by_id(
    request: Request,
    account_number: str,
    transaction_id: str,
    current_user=Depends(authenticated_user),
    db=Depends(get_db)
):
    """Fetch transaction by ID with concurrent validation."""
    try:
        # Validate formats
        if not SecurityUtils.validate_account_number(account_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account number format"
            )
        
        if not SecurityUtils.validate_transaction_id(transaction_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transaction ID format"
            )
        
        user_id = current_user.get('sub')
        
        # Create services
        account_service = AccountService(db)
        transaction_service = TransactionService(db, account_service)
        
        # Perform account and transaction lookups concurrently
        account_task = asyncio.create_task(
            account_service.get_account_by_number(account_number)
        )
        transaction_task = asyncio.create_task(
            transaction_service.get_transaction_by_id(account_number, transaction_id)
        )
        
        account, transaction = await asyncio.gather(account_task, transaction_task)
        
        # Validate results
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account was not found"
            )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check ownership
        user_permissions = getattr(request.state, 'permissions', [])
        if (account.user_id != user_id and 
            not any(perm in user_permissions for perm in ['admin', 'transaction:read:all'])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user is not allowed to access the transaction"
            )
        
        return TransactionResponse.from_orm(transaction)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch transaction {transaction_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/{account_number}/transactions/batch",
    response_model=List[TransactionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple transactions",
    description="Create multiple transactions concurrently (demo endpoint)"
)
@require_authentication
@require_permissions(["transaction:write", "admin"])  # Admin only for batch operations
async def create_batch_transactions(
    request: Request,
    account_number: str,
    transactions_data: List[CreateTransactionRequest],
    current_user=Depends(authenticated_user),
    db=Depends(get_db)
):
    """Create multiple transactions using concurrency patterns."""
    try:
        # Limit batch size for safety
        if len(transactions_data) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size cannot exceed 10 transactions"
            )
        
        user_id = current_user.get('sub')
        
        # Create services
        account_service = AccountService(db)
        transaction_service = TransactionService(db, account_service)
        
        # Verify account exists and ownership
        account = await account_service.get_account_by_number(account_number)
        if not account or account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or access denied"
            )
        
        # Create transaction entities
        transactions = []
        for tx_data in transactions_data:
            transaction = Transaction(
                id=SecurityUtils.generate_transaction_id(),
                account_number=account_number,
                amount=tx_data.amount,
                currency=tx_data.currency,
                type=tx_data.type,
                reference=tx_data.reference,
                user_id=user_id
            )
            transactions.append(transaction)
        
        # Process transactions concurrently
        async def process_transaction(tx):
            return await transaction_service.create_transaction(tx, user_id)
        
        # Use semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(3)
        
        async def limited_process(tx):
            async with semaphore:
                return await process_transaction(tx)
        
        # Execute all transactions
        tasks = [limited_process(tx) for tx in transactions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_transactions = []
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            else:
                successful_transactions.append(result)
        
        # Log any errors
        if errors:
            logger.warning(f"Some transactions failed: {errors}")
        
        # Convert to response models
        responses = [TransactionResponse.from_orm(tx) for tx in successful_transactions]
        
        logger.info(f"Batch processed: {len(successful_transactions)}/{len(transactions)} successful")
        
        return responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch transaction processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch processing failed"
        )
