"""Users API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
import logging

from app.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    ErrorResponse,
    BadRequestErrorResponse,
    UnauthorizedErrorResponse,
    ForbiddenErrorResponse,
    NotFoundErrorResponse,
)
from app.auth import (
    require_authentication,
    require_permissions,
    authenticated_user,
    admin_user,
    get_current_user,
)
from app.domain.services import UserService
from app.domain.entities import User
from app.api.dependencies import get_db
from app.core.security import SecurityUtils, audit_log


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": BadRequestErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Create a new user",
    description="Create a new user in the system",
)
async def create_user(
    request: Request, user_data: CreateUserRequest, db=Depends(get_db)
):
    """Create a new user."""
    try:
        # Create user repository and service
        from app.infrastructure.repositories import UserRepository

        user_repository = UserRepository(db)
        user_service = UserService(user_repository)

        # Generate user ID
        user_id = SecurityUtils.generate_user_id()

        # Create user entity
        user = User(
            id=user_id,
            name=user_data.name,
            address=user_data.address.dict(),
            phone_number=user_data.phone_number,
            email=user_data.email,
        )

        # Save user
        created_user = user_service.create_user(user)

        # Publish event
        if hasattr(request.app, "publish_event"):
            await request.app.publish_event(
                "user.created",
                {
                    "user_id": created_user.id,
                    "email": created_user.email,
                    "name": created_user.name,
                },
            )

        logger.info(f"User created successfully: {created_user.id}")

        return UserResponse.from_orm(created_user)

    except ValueError as e:
        logger.warning(f"User creation validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"User creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        400: {"model": BadRequestErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Fetch user by ID",
    description="Retrieve user details by user ID",
)
@require_authentication
@require_permissions(["user:read"])
@audit_log("fetch_user")
async def fetch_user_by_id(
    request: Request,
    user_id: str,
    current_user=Depends(authenticated_user),
    db=Depends(get_db),
):
    """Fetch user by ID."""
    try:
        # Validate user ID format
        if not SecurityUtils.validate_user_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
            )

        # Create user service
        from app.infrastructure.repositories import UserRepository

        user_repository = UserRepository(db)
        user_service = UserService(user_repository)

        # Get user
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check authorization (users can only access their own data unless admin)
        current_user_id = current_user.get("sub")
        user_permissions = getattr(request.state, "permissions", [])

        if user_id != current_user_id and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        return UserResponse.from_orm(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        400: {"model": BadRequestErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Update user by ID",
    description="Update user details by user ID",
)
@require_authentication
@require_permissions(["user:write"])
@audit_log("update_user")
async def update_user_by_id(
    request: Request,
    user_id: str,
    user_data: UpdateUserRequest,
    current_user=Depends(authenticated_user),
    db=Depends(get_db),
):
    """Update user by ID."""
    try:
        # Validate user ID format
        if not SecurityUtils.validate_user_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
            )

        # Create user service
        from app.infrastructure.repositories import UserRepository

        user_repository = UserRepository(db)
        user_service = UserService(user_repository)

        # Check if user exists
        existing_user = user_service.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check authorization
        current_user_id = current_user.get("sub")
        user_permissions = getattr(request.state, "permissions", [])

        if user_id != current_user_id and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        # Update user
        update_data = user_data.dict(exclude_unset=True)
        updated_user = user_service.update_user(user_id, update_data)

        # Publish event
        if hasattr(request.app, "publish_event"):
            await request.app.publish_event(
                "user.updated",
                {
                    "user_id": updated_user.id,
                    "updated_fields": list(update_data.keys()),
                },
            )

        logger.info(f"User updated successfully: {user_id}")

        return UserResponse.from_orm(updated_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": BadRequestErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Delete user by ID",
    description="Delete user by user ID",
)
@require_authentication
@require_permissions(["user:delete"])
@audit_log("delete_user")
async def delete_user_by_id(
    request: Request,
    user_id: str,
    current_user=Depends(admin_user),  # Only admins can delete users
    db=Depends(get_db),
):
    """Delete user by ID."""
    try:
        # Validate user ID format
        if not SecurityUtils.validate_user_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
            )

        # Create user service
        from app.infrastructure.repositories import UserRepository

        user_repository = UserRepository(db)
        user_service = UserService(user_repository)

        # Check if user exists
        existing_user = user_service.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check if user has associated accounts
        if user_service.user_has_accounts(user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A user cannot be deleted when they are associated "
                    "with a bank account"
                ),
            )

        # Delete user
        user_service.delete_user(user_id)

        # Publish event
        if hasattr(request.app, "publish_event"):
            await request.app.publish_event(
                "user.deleted",
                {"user_id": user_id, "deleted_by": current_user.get("sub")},
            )

        logger.info(f"User deleted successfully: {user_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
