from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_admin, get_current_user, get_user_repository
from app.repositories.user import UserRepository
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import UserAdminUpdate, UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


# ─────────────────────────────────────────────
# Current User Endpoints
# ─────────────────────────────────────────────


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    """Get the current user's profile."""
    return UserResponse.from_document(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the profile of the currently authenticated user.",
)
async def update_me(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserResponse:
    """Update the current user's profile."""
    user_service = UserService(user_repo)
    return await user_service.update_profile(current_user["_id"], data)


# ─────────────────────────────────────────────
# Admin Endpoints
# ─────────────────────────────────────────────


@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="List all users (Admin)",
    description="Get a paginated list of all users. Requires admin role.",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    admin: dict = Depends(get_current_admin),
    user_repo: UserRepository = Depends(get_user_repository),
) -> PaginatedResponse:
    """List all users with pagination (admin only)."""
    user_service = UserService(user_repo)
    return await user_service.get_users(page=page, page_size=page_size)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (Admin)",
    description="Get a specific user's details. Requires admin role.",
)
async def get_user(
    user_id: str,
    admin: dict = Depends(get_current_admin),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserResponse:
    """Get a user by ID (admin only)."""
    user_service = UserService(user_repo)
    return await user_service.get_user_by_id(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user (Admin)",
    description="Update a user's details including role and status. Requires admin role.",
)
async def update_user(
    user_id: str,
    data: UserAdminUpdate,
    admin: dict = Depends(get_current_admin),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserResponse:
    """Update a user (admin only)."""
    user_service = UserService(user_repo)
    return await user_service.admin_update_user(user_id, data)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete user (Admin)",
    description="Permanently delete a user. Requires admin role.",
)
async def delete_user(
    user_id: str,
    admin: dict = Depends(get_current_admin),
    user_repo: UserRepository = Depends(get_user_repository),
) -> MessageResponse:
    """Delete a user (admin only)."""
    user_service = UserService(user_repo)
    await user_service.delete_user(user_id)
    return MessageResponse(message="User deleted successfully")
