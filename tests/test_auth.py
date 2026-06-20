from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.security import create_verification_token, create_password_reset_token, hash_password
from app.database import Database
from app.models.user import UserDocument


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient) -> None:
    """Test user registration sends verification email and registers user in inactive/unverified state."""
    payload = {
        "email": "user@example.com",
        "password": "strongpassword123",
        "first_name": "John",
        "last_name": "Doe",
    }

    with patch("app.routes.auth.send_verification_email_task.delay") as mock_task:
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "user@example.com"
        assert data["first_name"] == "John"
        assert data["is_verified"] is False
        assert data["is_active"] is True
        mock_task.assert_called_once()


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Test registering with an already existing email fails."""
    db = Database.get_db()
    # Pre-insert user
    user_doc = UserDocument.create(
        email="user@example.com",
        hashed_password=hash_password("password"),
        first_name="First",
        last_name="Last",
    )
    await db.users.insert_one(user_doc)

    payload = {
        "email": "user@example.com",
        "password": "strongpassword123",
        "first_name": "John",
        "last_name": "Doe",
    }

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_email_success(client: AsyncClient) -> None:
    """Test email verification activates user and triggers welcome email."""
    db = Database.get_db()
    user_doc = UserDocument.create(
        email="unverified@example.com",
        hashed_password=hash_password("password"),
        first_name="Unverified",
        last_name="User",
    )
    await db.users.insert_one(user_doc)

    token = create_verification_token(user_doc["_id"])

    with patch("app.routes.auth.send_welcome_email_task.delay") as mock_task:
        response = await client.post("/api/v1/auth/verify-email", json={"token": token})
        assert response.status_code == 200
        assert response.json()["message"] == "Email address verified successfully"
        mock_task.assert_called_once_with("unverified@example.com", "Unverified")

    # Verify DB update
    user = await db.users.find_one({"_id": user_doc["_id"]})
    assert user["is_verified"] is True


@pytest.mark.asyncio
async def test_login_unverified_fails(client: AsyncClient) -> None:
    """Test login fails if email is not verified."""
    db = Database.get_db()
    user_doc = UserDocument.create(
        email="unverified@example.com",
        hashed_password=hash_password("password"),
        first_name="Unverified",
        last_name="User",
    )
    await db.users.insert_one(user_doc)

    payload = {"email": "unverified@example.com", "password": "password"}
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Email not verified" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_verified_success(client: AsyncClient) -> None:
    """Test login succeeds for verified active users."""
    db = Database.get_db()
    user_doc = UserDocument.create(
        email="verified@example.com",
        hashed_password=hash_password("password"),
        first_name="Verified",
        last_name="User",
    )
    user_doc["is_verified"] = True
    await db.users.insert_one(user_doc)

    payload = {"email": "verified@example.com", "password": "password"}
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_forgot_password_success(client: AsyncClient) -> None:
    """Test forgot password requests triggers reset email."""
    db = Database.get_db()
    user_doc = UserDocument.create(
        email="user@example.com",
        hashed_password=hash_password("password"),
        first_name="John",
        last_name="Doe",
    )
    user_doc["is_verified"] = True
    await db.users.insert_one(user_doc)

    with patch("app.routes.auth.send_reset_password_email_task.delay") as mock_task:
        response = await client.post("/api/v1/auth/forgot-password", json={"email": "user@example.com"})
        assert response.status_code == 200
        mock_task.assert_called_once()


@pytest.mark.asyncio
async def test_reset_password_success(client: AsyncClient) -> None:
    """Test reset password updates user password."""
    db = Database.get_db()
    user_doc = UserDocument.create(
        email="user@example.com",
        hashed_password=hash_password("password"),
        first_name="John",
        last_name="Doe",
    )
    await db.users.insert_one(user_doc)

    token = create_password_reset_token(user_doc["_id"])

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "newsecurepassword123"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"

    # Verify database update
    updated_user = await db.users.find_one({"_id": user_doc["_id"]})
    from app.core.security import verify_password
    assert verify_password("newsecurepassword123", updated_user["hashed_password"])
