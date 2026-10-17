from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import jwt
from fastapi.testclient import TestClient

from app.api import dependencies
from app.api.v1 import analyses
from app.api.v1 import auth
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.analysis import Analysis
from app.models.user import User
from app.services.users import DuplicateUserError


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_allows_frontend_localhost_cors_headers() -> None:
    client = TestClient(app)

    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


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


def test_list_analyses_only_returns_current_users_records(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = User(
        id=uuid4(),
        name="Current user",
        email="current@example.com",
        password_hash="not-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    other_user = User(
        id=uuid4(),
        name="Other user",
        email="other@example.com",
        password_hash="not-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    owned_analysis = Analysis(
        id=uuid4(),
        user_id=current_user.id,
        title="My analysis",
        status="queued",
        storage_key="private/my-video.mp4",
        original_filename="my-video.mp4",
        created_at=datetime.now(UTC),
    )
    other_analysis = Analysis(
        id=uuid4(),
        user_id=other_user.id,
        title="Other analysis",
        status="queued",
        storage_key="private/other-video.mp4",
        original_filename="other-video.mp4",
        created_at=datetime.now(UTC),
    )

    class FakeResult:
        def all(self) -> list[Analysis]:
            return [owned_analysis]

    class FakeSession:
        def scalars(self, statement):
            compiled = statement.compile()
            assert current_user.id in compiled.params.values()
            assert "analyses.user_id =" in str(compiled)
            return FakeResult()

    def fake_db():
        yield FakeSession()

    monkeypatch.setitem(
        app.dependency_overrides,
        dependencies.get_current_user,
        lambda: current_user,
    )
    monkeypatch.setitem(app.dependency_overrides, get_db, fake_db)
    response = client.get("/api/v1/analyses")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [str(owned_analysis.id)]
    assert response.json()[0]["title"] == "My analysis"
    assert "storage_key" not in response.json()[0]
    assert other_analysis.id not in {UUID(item["id"]) for item in response.json()}


def test_create_analysis_returns_created_record(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = User(
        id=uuid4(),
        name="Current user",
        email="current@example.com",
        password_hash="not-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class FakeSession:
        def add(self, analysis: Analysis) -> None:
            assert analysis.user_id == current_user.id
            assert analysis.title == "Minha palestra"
            assert analysis.status == "queued"
            assert analysis.original_filename == "pitch.mp4"
            assert analysis.language == "pt"
            assert analysis.analysis_goal == "Treinar presença"

        def commit(self) -> None:
            return None

        def refresh(self, analysis: Analysis) -> None:
            analysis.created_at = datetime.now(UTC)

    def fake_db():
        yield FakeSession()

    monkeypatch.setitem(
        app.dependency_overrides,
        dependencies.get_current_user,
        lambda: current_user,
    )
    monkeypatch.setitem(app.dependency_overrides, get_db, fake_db)
    response = client.post(
        "/api/v1/analyses",
        json={
            "title": "Minha palestra",
            "storage_key": "private/pitch.mp4",
            "original_filename": "pitch.mp4",
            "language": "pt",
            "analysis_goal": "Treinar presença",
        },
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Minha palestra"
    assert response.json()["status"] == "queued"
    assert response.json()["original_filename"] == "pitch.mp4"
    assert response.json()["analysis_goal"] == "Treinar presença"


def test_upload_analysis_saves_file_and_returns_analysis(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = User(
        id=uuid4(),
        name="Current user",
        email="current@example.com",
        password_hash="not-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class FakeSession:
        def add(self, obj: object) -> None:
            return None

        def commit(self) -> None:
            return None

        def refresh(self, obj: object) -> None:
            return None

    def fake_db():
        yield FakeSession()

    monkeypatch.setitem(
        app.dependency_overrides,
        dependencies.get_current_user,
        lambda: current_user,
    )
    monkeypatch.setitem(app.dependency_overrides, get_db, fake_db)

    response = client.post(
        "/api/v1/analyses/upload",
        files={"file": ("pitch.mp4", b"fake-video-bytes", "video/mp4")},
        data={
            "title": "Pitch da startup",
            "language": "pt",
            "analysis_goal": "Treinar presença",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Pitch da startup"
    assert payload["original_filename"] == "pitch.mp4"
    assert payload["status"] == "queued"
    files = list((Path(__file__).resolve().parents[2] / "storage" / "uploads").glob("*.mp4"))
    assert files
    assert files[0].name.endswith(".mp4")


def test_generate_report_returns_summary_and_score(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = User(
        id=uuid4(),
        name="Current user",
        email="current@example.com",
        password_hash="not-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    analysis = Analysis(
        id=uuid4(),
        user_id=current_user.id,
        title="Apresentação interna",
        status="queued",
        storage_key="private/presentation.mp4",
        original_filename="presentation.mp4",
        created_at=datetime.now(UTC),
    )

    class FakeSession:
        def scalar(self, statement) -> Analysis:
            compiled = statement.compile()
            assert current_user.id in compiled.params.values()
            assert analysis.id in compiled.params.values()
            return analysis

        def add(self, obj: object) -> None:
            return None

        def add_all(self, objs: list[object]) -> None:
            assert len(objs) == 3

        def commit(self) -> None:
            return None

        def refresh(self, obj: object) -> None:
            return None

    def fake_db():
        yield FakeSession()

    monkeypatch.setitem(
        app.dependency_overrides,
        dependencies.get_current_user,
        lambda: current_user,
    )
    monkeypatch.setitem(app.dependency_overrides, get_db, fake_db)
    response = client.post(
        f"/api/v1/analyses/{analysis.id}/report",
        json={
            "segments": [
                {"start": 0, "end": 2, "text": "Olá, ahn eu eu"},
                {"start": 2.5, "end": 4.5, "text": "vamos começar."},
            ],
            "language": "pt",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_id"] == str(analysis.id)
    assert 0 <= payload["overall_score"] <= 100
    assert payload["summary"]
    assert payload["highlights"]


def test_get_analysis_returns_owned_analysis(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = User(
        id=uuid4(),
        name="Current user",
        email="current@example.com",
        password_hash="not-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    analysis = Analysis(
        id=uuid4(),
        user_id=current_user.id,
        title="My analysis",
        status="queued",
        storage_key="private/my-video.mp4",
        original_filename="my-video.mp4",
        created_at=datetime.now(UTC),
    )

    class FakeSession:
        def scalar(self, statement) -> Analysis:
            compiled = statement.compile()
            assert current_user.id in compiled.params.values()
            assert analysis.id in compiled.params.values()
            assert "analyses.id =" in str(compiled)
            assert "analyses.user_id =" in str(compiled)
            return analysis

    def fake_db():
        yield FakeSession()

    monkeypatch.setitem(
        app.dependency_overrides,
        dependencies.get_current_user,
        lambda: current_user,
    )
    monkeypatch.setitem(app.dependency_overrides, get_db, fake_db)
    response = client.get(f"/api/v1/analyses/{analysis.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(analysis.id)
    assert response.json()["title"] == "My analysis"
    assert "storage_key" not in response.json()


def test_get_analysis_hides_records_owned_by_other_users(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = User(
        id=uuid4(),
        name="Current user",
        email="current@example.com",
        password_hash="not-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    other_user = User(
        id=uuid4(),
        name="Other user",
        email="other@example.com",
        password_hash="not-returned",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    other_analysis = Analysis(
        id=uuid4(),
        user_id=other_user.id,
        title="Private analysis",
        status="queued",
        storage_key="private/other-video.mp4",
        original_filename="other-video.mp4",
        created_at=datetime.now(UTC),
    )

    class FakeSession:
        def scalar(self, statement) -> None:
            compiled = statement.compile()
            assert current_user.id in compiled.params.values()
            assert other_analysis.id in compiled.params.values()
            assert "analyses.id =" in str(compiled)
            assert "analyses.user_id =" in str(compiled)
            return None

    def fake_db():
        yield FakeSession()

    monkeypatch.setitem(
        app.dependency_overrides,
        dependencies.get_current_user,
        lambda: current_user,
    )
    monkeypatch.setitem(app.dependency_overrides, get_db, fake_db)
    response = client.get(f"/api/v1/analyses/{other_analysis.id}")

    assert response.status_code == 404