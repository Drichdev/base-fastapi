import pytest
from httpx import AsyncClient

from app.core.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.database import Database
from app.models.user import UserDocument


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient) -> None:
    """Test retrieving profile without authentication fails."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401  # now raises 401 instead of validation error
    response = await client.get("/api/v1/users/me", headers={"Authorization": "InvalidFormat"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient) -> None:
    """Test retrieving profile with valid credentials."""
    db = Database.get_db()
    user_doc = UserDocument.create(
        email="user@example.com",
        hashed_password=hash_password("password"),
        first_name="John",
        last_name="Doe",
    )
    user_doc["is_verified"] = True
    await db.users.insert_one(user_doc)

    token = create_access_token(user_doc["_id"], UserRole.USER)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["first_name"] == "John"


@pytest.mark.asyncio
async def test_update_me_success(client: AsyncClient) -> None:
    """Test user can update their own profile."""
    db = Database.get_db()
    user_doc = UserDocument.create(
        email="user@example.com",
        hashed_password=hash_password("password"),
        first_name="John",
        last_name="Doe",
    )
    user_doc["is_verified"] = True
    await db.users.insert_one(user_doc)

    token = create_access_token(user_doc["_id"], UserRole.USER)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"first_name": "Johnny", "last_name": "Doey"}
    response = await client.put("/api/v1/users/me", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Johnny"
    assert data["last_name"] == "Doey"


@pytest.mark.asyncio
async def test_list_users_non_admin_forbidden(client: AsyncClient) -> None:
    """Test regular users cannot list all users."""
    db = Database.get_db()
    user_doc = UserDocument.create(
        email="user@example.com",
        hashed_password=hash_password("password"),
        first_name="John",
        last_name="Doe",
    )
    user_doc["is_verified"] = True
    await db.users.insert_one(user_doc)

    token = create_access_token(user_doc["_id"], UserRole.USER)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 403
    assert "Admin access required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_users_admin_success(client: AsyncClient) -> None:
    """Test admin users can list all users."""
    db = Database.get_db()
    admin_doc = UserDocument.create(
        email="admin@example.com",
        hashed_password=hash_password("password"),
        first_name="Admin",
        last_name="System",
        role=UserRole.ADMIN,
    )
    admin_doc["is_verified"] = True
    await db.users.insert_one(admin_doc)

    token = create_access_token(admin_doc["_id"], UserRole.ADMIN)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["email"] == "admin@example.com"


@pytest.mark.asyncio
async def test_admin_update_user(client: AsyncClient) -> None:
    """Test admin users can update any user."""
    db = Database.get_db()
    admin_doc = UserDocument.create(
        email="admin@example.com",
        hashed_password=hash_password("password"),
        first_name="Admin",
        last_name="System",
        role=UserRole.ADMIN,
    )
    admin_doc["is_verified"] = True
    await db.users.insert_one(admin_doc)

    user_doc = UserDocument.create(
        email="user@example.com",
        hashed_password=hash_password("password"),
        first_name="John",
        last_name="Doe",
    )
    await db.users.insert_one(user_doc)

    token = create_access_token(admin_doc["_id"], UserRole.ADMIN)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"role": UserRole.ADMIN, "is_verified": True}
    response = await client.put(f"/api/v1/users/{user_doc['_id']}", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == UserRole.ADMIN
    assert data["is_verified"] is True


@pytest.mark.asyncio
async def test_admin_delete_user(client: AsyncClient) -> None:
    """Test admin users can delete any user."""
    db = Database.get_db()
    admin_doc = UserDocument.create(
        email="admin@example.com",
        hashed_password=hash_password("password"),
        first_name="Admin",
        last_name="System",
        role=UserRole.ADMIN,
    )
    admin_doc["is_verified"] = True
    await db.users.insert_one(admin_doc)

    user_doc = UserDocument.create(
        email="user@example.com",
        hashed_password=hash_password("password"),
        first_name="John",
        last_name="Doe",
    )
    await db.users.insert_one(user_doc)

    token = create_access_token(admin_doc["_id"], UserRole.ADMIN)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.delete(f"/api/v1/users/{user_doc['_id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"

    # Verify deleted from DB
    user = await db.users.find_one({"_id": user_doc["_id"]})
    assert user is None
