from datetime import UTC, datetime
from uuid import uuid4

import pytest
import jwt
from fastapi.testclient import TestClient

from app.api import dependencies
from app.api.v1 import auth
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.services.users import DuplicateUserError


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_register_returns_user_without_password_hash(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = User(
        id=uuid4(),
        name="Bruno",
        email="bruno@example.com",
        password_hash="must-not-be-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    def fake_create_user(username: str, password: str, email: str) -> User:
        assert username == "Bruno"
        assert password == "strong-password"
        assert email == "bruno@example.com"
        return user

    monkeypatch.setattr(auth, "create_user", fake_create_user)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": " Bruno ",
            "email": "bruno@example.com",
            "password": "strong-password",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(user.id)
    assert response.json()["name"] == "Bruno"
    assert "password_hash" not in response.json()


def test_register_returns_conflict_for_duplicate_email(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_duplicate(**_: str) -> User:
        raise DuplicateUserError("Já existe um usuário com este e-mail.")

    monkeypatch.setattr(auth, "create_user", raise_duplicate)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Bruno",
            "email": "bruno@example.com",
            "password": "strong-password",
        },
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"name": " ", "email": "bruno@example.com", "password": "strong-password"},
        {"name": "Bruno", "email": "invalid-email", "password": "strong-password"},
        {"name": "Bruno", "email": "bruno@example.com", "password": "short"},
    ],
)
def test_register_rejects_invalid_payload(
    client: TestClient,
    payload: dict[str, str],
) -> None:
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422


def test_login_returns_expiring_bearer_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = User(
        id=uuid4(),
        name="Bruno",
        email="bruno@example.com",
        password_hash="not-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    monkeypatch.setattr(auth, "authenticate_user", lambda **_: user)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "bruno@example.com", "password": "strong-password"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["expires_in"] == settings.access_token_expire_minutes * 60
    claims = jwt.decode(
        response.json()["access_token"],
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    assert claims["sub"] == str(user.id)


def test_login_rejects_invalid_credentials(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth, "authenticate_user", lambda **_: None)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "bruno@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_users_me_returns_authenticated_user(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = User(
        id=uuid4(),
        name="Bruno",
        email="bruno@example.com",
        password_hash="must-not-be-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class FakeSession:
        def get(self, model: type[User], user_id: object) -> User | None:
            if model is User and user_id == user.id:
                return user
            return None

    def fake_db():
        yield FakeSession()

    monkeypatch.setitem(app.dependency_overrides, get_db, fake_db)
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {create_access_token(str(user.id))}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    assert "password_hash" not in response.json()


@pytest.mark.parametrize("authorization", [None, "Bearer invalid-token"])
def test_users_me_rejects_missing_or_invalid_token(
    client: TestClient,
    authorization: str | None,
) -> None:
    headers = {"Authorization": authorization} if authorization else {}
    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"