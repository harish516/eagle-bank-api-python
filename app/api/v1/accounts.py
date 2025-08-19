"""Accounts API endpoints with advanced patterns."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
import asyncio
import logging

from app.schemas import (
    CreateBankAccountRequest,
    UpdateBankAccountRequest,
    BankAccountResponse,
    ListBankAccountsResponse,
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
    admin_user,
    get_current_user
)
from app.domain.services import AccountService, UserService
from app.domain.entities import Account, AccountType
from app.api.dependencies import get_db
from app.core.security import SecurityUtils, audit_log, rate_limit


logger = logging.getLogger(__name__)
router = APIRouter()


class AccountFactory:
    """Factory pattern for creating different types of accounts."""
    
    @staticmethod
    def create_account(
        account_type: AccountType,
        name: str,
        account_number: str = None
    ) -> Account:
        """Factory method to create accounts."""
        if not account_number:
            account_number = SecurityUtils.generate_account_number()
        
        # For now, we only support personal accounts
        # In the future, we could add business accounts, savings accounts, etc.
        if account_type == AccountType.PERSONAL:
            return Account(
                account_number=account_number,
                name=name,
                account_type=account_type
            )
        else:
            raise ValueError(f"Unsupported account type: {account_type}")


class AccountFacade:
    """Facade pattern for simplifying account operations."""
    
    def __init__(self, account_service: AccountService, user_service: UserService):
        self.account_service = account_service
        self.user_service = user_service
    
    async def create_account_for_user(
        self,
        user_id: str,
        account_data: CreateBankAccountRequest
    ) -> Account:
        """Simplified interface for creating an account."""
        # Validate user exists
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Create account using factory
        account = AccountFactory.create_account(
            account_data.account_type,
            account_data.name
        )
        
        # Save account
        return await self.account_service.create_account(account, user_id)
    
    async def get_user_accounts(self, user_id: str) -> List[Account]:
        """Get all accounts for a user."""
        return await self.account_service.get_accounts_by_user(user_id)


@router.post(
    "",
    response_model=BankAccountResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": BadRequestErrorResponse},
        401: {"model": UnauthorizedErrorResponse},
        403: {"model": ForbiddenErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Create a new bank account",
    description="Create a new bank account for the authenticated user"
)
@require_authentication
@require_permissions(["account:write"])
@rate_limit(calls_per_minute=10)  # Rate limit account creation
@audit_log("create_account")
async def create_account(
    request: Request,
    account_data: CreateBankAccountRequest,
    current_user=Depends(authenticated_user),
    db=Depends(get_db)
):
    """Create a new bank account."""
    try:
        user_id = current_user.get('sub')
        
        # Create services
        account_service = AccountService(db)
        user_service = UserService(db)
        
        # Use facade for simplified account creation
        facade = AccountFacade(account_service, user_service)
        created_account = await facade.create_account_for_user(user_id, account_data)
        
        # Publish event
        if hasattr(request.app, 'publish_event'):
            await request.app.publish_event(
                "account.created",
                {
                    "account_number": created_account.account_number,
                    "user_id": user_id,
                    "account_type": created_account.account_type.value
                }
            )
        
        logger.info(f"Account created: {created_account.account_number}")
        
        return BankAccountResponse.from_orm(created_account)
        
    except ValueError as e:
        logger.warning(f"Account creation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Account creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "",
    response_model=ListBankAccountsResponse,
    responses={
        401: {"model": UnauthorizedErrorResponse},
        403: {"model": ForbiddenErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="List accounts",
    description="List all bank accounts for the authenticated user"
)
@require_authentication
@require_permissions(["account:read"])
async def list_accounts(
    request: Request,
    current_user=Depends(authenticated_user),
    db=Depends(get_db)
):
    """List accounts for the current user."""
    try:
        user_id = current_user.get('sub')
        
        # Create services
        account_service = AccountService(db)
        user_service = UserService(db)
        
        # Use facade for simplified account retrieval
        facade = AccountFacade(account_service, user_service)
        accounts = await facade.get_user_accounts(user_id)
        
        # Convert to response models
        account_responses = [BankAccountResponse.from_orm(acc) for acc in accounts]
        
        return ListBankAccountsResponse(accounts=account_responses)
        
    except Exception as e:
        logger.error(f"Failed to list accounts for user {current_user.get('sub')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/{account_number}",
    response_model=BankAccountResponse,
    responses={
        400: {"model": BadRequestErrorResponse},
        401: {"model": UnauthorizedErrorResponse},
        403: {"model": ForbiddenErrorResponse},
        404: {"model": NotFoundErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Fetch account by account number",
    description="Retrieve bank account details by account number"
)
@require_authentication
@require_permissions(["account:read"])
@audit_log("fetch_account")
async def fetch_account_by_account_number(
    request: Request,
    account_number: str,
    current_user=Depends(authenticated_user),
    db=Depends(get_db)
):
    """Fetch account by account number."""
    try:
        # Validate account number format
        if not SecurityUtils.validate_account_number(account_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account number format"
            )
        
        user_id = current_user.get('sub')
        account_service = AccountService(db)
        
        # Get account
        account = await account_service.get_account_by_number(account_number)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account was not found"
            )
        
        # Check ownership (users can only access their own accounts unless admin)
        user_permissions = getattr(request.state, 'permissions', [])
        if (account.user_id != user_id and 
            not any(perm in user_permissions for perm in ['admin', 'account:read:all'])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user is not allowed to access the bank account details"
            )
        
        return BankAccountResponse.from_orm(account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch account {account_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.patch(
    "/{account_number}",
    response_model=BankAccountResponse,
    responses={
        400: {"model": BadRequestErrorResponse},
        401: {"model": UnauthorizedErrorResponse},
        403: {"model": ForbiddenErrorResponse},
        404: {"model": NotFoundErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Update account by account number",
    description="Update bank account details by account number"
)
@require_authentication
@require_permissions(["account:write"])
@audit_log("update_account")
async def update_account_by_account_number(
    request: Request,
    account_number: str,
    account_data: UpdateBankAccountRequest,
    current_user=Depends(authenticated_user),
    db=Depends(get_db)
):
    """Update account by account number."""
    try:
        # Validate account number format
        if not SecurityUtils.validate_account_number(account_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account number format"
            )
        
        user_id = current_user.get('sub')
        account_service = AccountService(db)
        
        # Check if account exists and user ownership
        account = await account_service.get_account_by_number(account_number)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account was not found"
            )
        
        # Check ownership
        user_permissions = getattr(request.state, 'permissions', [])
        if (account.user_id != user_id and 
            not any(perm in user_permissions for perm in ['admin', 'account:write:all'])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user is not allowed to update the bank account details"
            )
        
        # Update account
        update_data = account_data.dict(exclude_unset=True)
        updated_account = await account_service.update_account(account_number, update_data)
        
        # Publish event
        if hasattr(request.app, 'publish_event'):
            await request.app.publish_event(
                "account.updated",
                {
                    "account_number": account_number,
                    "user_id": user_id,
                    "updated_fields": list(update_data.keys())
                }
            )
        
        logger.info(f"Account updated: {account_number}")
        
        return BankAccountResponse.from_orm(updated_account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update account {account_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.delete(
    "/{account_number}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": BadRequestErrorResponse},
        401: {"model": UnauthorizedErrorResponse},
        403: {"model": ForbiddenErrorResponse},
        404: {"model": NotFoundErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Delete account by account number",
    description="Delete bank account by account number"
)
@require_authentication
@require_permissions(["account:delete"])
@audit_log("delete_account")
async def delete_account_by_account_number(
    request: Request,
    account_number: str,
    current_user=Depends(authenticated_user),
    db=Depends(get_db)
):
    """Delete account by account number."""
    try:
        # Validate account number format
        if not SecurityUtils.validate_account_number(account_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account number format"
            )
        
        user_id = current_user.get('sub')
        account_service = AccountService(db)
        
        # Check if account exists
        account = await account_service.get_account_by_number(account_number)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account was not found"
            )
        
        # Check ownership
        user_permissions = getattr(request.state, 'permissions', [])
        if (account.user_id != user_id and 
            not any(perm in user_permissions for perm in ['admin', 'account:delete:all'])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user is not allowed to delete the bank account details"
            )
        
        # Delete account
        await account_service.delete_account(account_number)
        
        # Publish event
        if hasattr(request.app, 'publish_event'):
            await request.app.publish_event(
                "account.deleted",
                {
                    "account_number": account_number,
                    "user_id": user_id,
                    "deleted_by": user_id
                }
            )
        
        logger.info(f"Account deleted: {account_number}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete account {account_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
