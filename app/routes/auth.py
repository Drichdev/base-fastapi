from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_user_repository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import AuthService
from app.tasks.email_tasks import (
    send_welcome_email_task,
    send_verification_email_task,
    send_reset_password_email_task,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user",
    description="Create a new user account. An email verification token will be sent asynchronously.",
)
async def register(
    data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserResponse:
    """Register a new user and send verification email via Celery."""
    auth_service = AuthService(user_repo)
    user, verification_token = await auth_service.register(data)

    # Send verification email asynchronously via Celery
    send_verification_email_task.delay(data.email, data.first_name, verification_token)

    return UserResponse.from_document(user)


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address",
    description="Verify email address using a verification token sent by email.",
)
async def verify_email(
    data: EmailVerificationRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> MessageResponse:
    """Verify user's email address."""
    auth_service = AuthService(user_repo)
    user = await auth_service.verify_email(data.token)

    # Send welcome email now that they are verified!
    send_welcome_email_task.delay(user["email"], user["first_name"])

    return MessageResponse(message="Email address verified successfully")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Request a password reset token to be sent to the user's email.",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> MessageResponse:
    """Request a password reset link/token."""
    auth_service = AuthService(user_repo)
    try:
        user, reset_token = await auth_service.forgot_password(data.email)
        send_reset_password_email_task.delay(user["email"], user["first_name"], reset_token)
    except Exception:
        # Ignore exception for security to prevent user enumeration
        pass

    return MessageResponse(message="If the email exists, a password reset link has been sent.")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password",
    description="Reset password using a valid reset token.",
)
async def reset_password(
    data: ResetPasswordRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> MessageResponse:
    """Reset user password."""
    auth_service = AuthService(user_repo)
    await auth_service.reset_password(data.token, data.new_password)
    return MessageResponse(message="Password reset successfully")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate with email and password. Returns JWT access and refresh tokens.",
)
async def login(
    data: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> TokenResponse:
    """Authenticate and return JWT tokens."""
    auth_service = AuthService(user_repo)
    return await auth_service.login(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token.",
)
async def refresh_token(
    data: RefreshRequest,
    user_repo: UserRepository = Depends(get_user_repository),
) -> TokenResponse:
    """Refresh the access token."""
    auth_service = AuthService(user_repo)
    return await auth_service.refresh(data.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Logout the current user. Client should discard the token.",
)
async def logout(
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    """Logout the current user.

    Note: With stateless JWT, the client is responsible for discarding the token.
    For production, consider adding token blacklisting via Redis.
    """
    return MessageResponse(message="Successfully logged out")

