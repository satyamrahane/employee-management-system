"""Authentication API tests use an isolated app and in-memory SQLite only."""

from datetime import datetime, timedelta, timezone
import uuid

import pytest
import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Column, String, Table, create_engine, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import auth_api
from app.auth_api import (
    AuthRequestSecurityMiddleware,
    AuthenticatedPrincipal,
    require_roles,
    router,
)
from app.auth_models import (
    AuthRefreshTokenHistoryModel,
    AuthSessionModel,
    RoleModel,
    UserModel,
    UserRoleModel,
)
from app.config import settings
from app.database import Base, get_db
from app.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_access_token,
)


TEST_ORIGIN = "http://testserver"
TEST_SECRET = "isolated-auth-api-test-signing-secret-has-more-than-32-bytes"


@pytest.fixture
def auth_environment(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_JWT_SECRET_KEY", TEST_SECRET)
    monkeypatch.setattr(settings, "AUTH_TRUSTED_ORIGINS", [TEST_ORIGIN])
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", False)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SAMESITE", "lax")
    monkeypatch.setattr(settings, "AUTH_LOGIN_MAX_FAILURES", 5)
    monkeypatch.setattr(settings, "AUTH_LOGIN_LOCKOUT_MINUTES", 15)
    monkeypatch.setattr(settings, "AUTH_REFRESH_TOKEN_EXPIRE_DAYS", 7)
    monkeypatch.setattr(settings, "AUTH_SESSION_EXPIRE_DAYS", 30)

    if "employees" not in Base.metadata.tables:
        Table(
            "employees",
            Base.metadata,
            Column("id", String(50), primary_key=True),
        )

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    app = FastAPI()
    app.add_middleware(AuthRequestSecurityMiddleware)
    app.include_router(router)

    def override_get_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    @app.get("/test/admin")
    def admin_probe(
        _principal: AuthenticatedPrincipal = Depends(
            require_roles("ADMIN")
        ),
    ):
        return {"allowed": True}

    with TestClient(app) as client:
        yield {"client": client, "factory": factory}

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _create_user(
    factory,
    *,
    email="person@example.test",
    password="correct horse battery staple",
    active=True,
    failed_login_count=0,
    locked_until=None,
    roles=("HR",),
):
    with factory.begin() as db:
        user = UserModel(
            email=email.strip().lower(),
            password_hash=hash_password(password),
            is_active=active,
            failed_login_count=failed_login_count,
            locked_until=locked_until,
        )
        db.add(user)
        db.flush()
        for role_name in roles:
            role = db.scalar(
                select(RoleModel).where(RoleModel.name == role_name)
            )
            if role is None:
                role = RoleModel(name=role_name)
                db.add(role)
                db.flush()
            db.add(UserRoleModel(user_id=user.id, role_id=role.id))
        db.flush()
        return user.id


def _create_session(factory, user_id, *, expires_at=None, revoked_at=None):
    now = datetime.now(timezone.utc)
    token = generate_refresh_token()
    absolute_expiry = expires_at or now + timedelta(days=30)
    with factory.begin() as db:
        auth_session = AuthSessionModel(
            user_id=user_id,
            token_hash=hash_refresh_token(token),
            issued_at=now,
            expires_at=absolute_expiry,
            current_refresh_expires_at=min(
                now + timedelta(days=7), absolute_expiry
            ),
            revoked_at=revoked_at,
        )
        db.add(auth_session)
        db.flush()
        return auth_session.id, token


def _origin_headers():
    return {"Origin": TEST_ORIGIN}


def _csrf_headers(csrf_token):
    return {
        **_origin_headers(),
        settings.AUTH_CSRF_HEADER_NAME: csrf_token,
    }


def _csrf_cookies(csrf_token):
    return {settings.AUTH_CSRF_COOKIE_NAME: csrf_token}


def test_login_sets_http_only_refresh_cookie_and_never_returns_raw_token(
    auth_environment,
):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    _create_user(factory, email="person@example.test")

    response = client.post(
        "/api/auth/login",
        json={
            "email": "  PERSON@EXAMPLE.TEST ",
            "password": "correct horse battery staple",
        },
        headers=_origin_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "access_token",
        "token_type",
        "expires_in",
        "csrf_token",
    }
    assert body["token_type"] == "bearer"
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "no-store"
    refresh_token = response.cookies[settings.AUTH_REFRESH_COOKIE_NAME]
    assert refresh_token not in response.text
    assert hash_refresh_token(refresh_token) not in response.text
    set_cookie = response.headers.get_list("set-cookie")
    refresh_cookie = next(
        value
        for value in set_cookie
        if value.startswith(f"{settings.AUTH_REFRESH_COOKIE_NAME}=")
    )
    assert "httponly" in refresh_cookie.lower()
    assert "secure" not in refresh_cookie.lower()
    assert "samesite=lax" in refresh_cookie.lower()
    assert f"path={settings.API_PREFIX}/auth" in refresh_cookie.lower()
    assert "domain=" not in refresh_cookie.lower()
    csrf_cookie = next(
        value
        for value in set_cookie
        if value.startswith(f"{settings.AUTH_CSRF_COOKIE_NAME}=")
    )
    assert "httponly" not in csrf_cookie.lower()
    assert "path=/;" in csrf_cookie.lower()

    with factory() as db:
        auth_session = db.scalar(select(AuthSessionModel))
    assert auth_session.token_hash == hash_refresh_token(refresh_token)
    assert auth_session.token_hash != refresh_token


def test_wrong_password_and_unknown_email_have_identical_responses(
    auth_environment,
):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    _create_user(factory)

    wrong_password = client.post(
        "/api/auth/login",
        json={
            "email": "person@example.test",
            "password": "incorrect password",
        },
        headers=_origin_headers(),
    )
    unknown_user = client.post(
        "/api/auth/login",
        json={
            "email": "missing@example.test",
            "password": "incorrect password",
        },
        headers=_origin_headers(),
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_inactive_and_locked_users_receive_generic_failure(auth_environment):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    _create_user(factory, email="inactive@example.test", active=False)
    _create_user(
        factory,
        email="locked@example.test",
        locked_until=datetime.now(timezone.utc) + timedelta(minutes=10),
    )

    inactive = client.post(
        "/api/auth/login",
        json={
            "email": "inactive@example.test",
            "password": "correct horse battery staple",
        },
        headers=_origin_headers(),
    )
    locked = client.post(
        "/api/auth/login",
        json={
            "email": "locked@example.test",
            "password": "correct horse battery staple",
        },
        headers=_origin_headers(),
    )

    assert inactive.status_code == locked.status_code == 401
    assert inactive.json() == locked.json()


def test_consecutive_failures_lock_account_and_success_resets_counter(
    auth_environment,
):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    user_id = _create_user(factory)

    for _ in range(settings.AUTH_LOGIN_MAX_FAILURES):
        response = client.post(
            "/api/auth/login",
            json={
                "email": "person@example.test",
                "password": "incorrect password",
            },
            headers=_origin_headers(),
        )
        assert response.status_code == 401

    with factory() as db:
        user = db.get(UserModel, user_id)
        assert user.failed_login_count == settings.AUTH_LOGIN_MAX_FAILURES
        assert user.locked_until is not None

    locked_response = client.post(
        "/api/auth/login",
        json={
            "email": "person@example.test",
            "password": "correct horse battery staple",
        },
        headers=_origin_headers(),
    )
    assert locked_response.status_code == 401


def test_login_fails_closed_without_trusted_origin_configuration(
    auth_environment,
    monkeypatch,
):
    monkeypatch.setattr(settings, "AUTH_TRUSTED_ORIGINS", [])
    response = auth_environment["client"].post(
        "/api/auth/login",
        json={
            "email": "person@example.test",
            "password": "correct horse battery staple",
        },
        headers=_origin_headers(),
    )
    assert response.status_code == 403


def test_login_failure_counter_write_does_not_create_a_session(
    auth_environment,
):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    user_id = _create_user(factory)

    response = client.post(
        "/api/auth/login",
        json={
            "email": "person@example.test",
            "password": "incorrect password",
        },
        headers=_origin_headers(),
    )

    assert response.status_code == 401
    with factory() as db:
        user = db.get(UserModel, user_id)
        session_count = len(db.scalars(select(AuthSessionModel.id)).all())
    assert user.failed_login_count == 1
    assert session_count == 0


def test_me_returns_current_identity_and_roles_only(auth_environment):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    user_id = _create_user(factory, email="person@example.test", roles=("HR",))
    session_id, _ = _create_session(factory, user_id)
    access_token = create_access_token(user_id=user_id, session_id=session_id)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": user_id,
        "email": "person@example.test",
        "roles": ["HR"],
    }
    assert "password_hash" not in response.text
    assert "token_hash" not in response.text
    assert response.headers["Cache-Control"] == "no-store"


def test_me_rejects_missing_invalid_expired_and_revoked_credentials(
    auth_environment,
):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    user_id = _create_user(factory)
    active_session_id, _ = _create_session(factory, user_id)
    revoked_session_id, _ = _create_session(
        factory,
        user_id,
        revoked_at=datetime.now(timezone.utc),
    )
    expired_session_id, _ = _create_session(
        factory,
        user_id,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )

    missing = client.get("/api/auth/me")
    invalid = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    now = datetime.now(timezone.utc)
    expired_access_token = jwt.encode(
        {
            "sub": user_id,
            "sid": active_session_id,
            "iss": settings.AUTH_JWT_ISSUER,
            "aud": settings.AUTH_JWT_AUDIENCE,
            "iat": now - timedelta(minutes=2),
            "nbf": now - timedelta(minutes=2),
            "exp": now - timedelta(minutes=1),
        },
        TEST_SECRET,
        algorithm="HS256",
    )
    expired_token_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_access_token}"},
    )
    revoked = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer "
            + create_access_token(
                user_id=user_id,
                session_id=revoked_session_id,
            )
        },
    )
    expired = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer "
            + create_access_token(
                user_id=user_id,
                session_id=expired_session_id,
            )
        },
    )
    active = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer "
            + create_access_token(
                user_id=user_id,
                session_id=active_session_id,
            )
        },
    )

    assert [
        missing.status_code,
        invalid.status_code,
        expired_token_response.status_code,
        revoked.status_code,
        expired.status_code,
    ] == [401, 401, 401, 401, 401]
    assert active.status_code == 200
    assert (
        missing.json()
        == invalid.json()
        == expired_token_response.json()
        == revoked.json()
        == expired.json()
    )


def test_me_rejects_inactive_user_even_with_valid_access_token(
    auth_environment,
):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    user_id = _create_user(factory, active=False)
    session_id, _ = _create_session(factory, user_id)
    access_token = create_access_token(user_id=user_id, session_id=session_id)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_role_dependency_enforces_database_roles(auth_environment):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    hr_user_id = _create_user(factory, email="hr@example.test", roles=("HR",))
    admin_user_id = _create_user(
        factory,
        email="admin@example.test",
        roles=("ADMIN",),
    )
    hr_session_id, _ = _create_session(factory, hr_user_id)
    admin_session_id, _ = _create_session(factory, admin_user_id)

    denied = client.get(
        "/test/admin",
        headers={
            "Authorization": "Bearer "
            + create_access_token(user_id=hr_user_id, session_id=hr_session_id)
        },
    )
    allowed = client.get(
        "/test/admin",
        headers={
            "Authorization": "Bearer "
            + create_access_token(
                user_id=admin_user_id,
                session_id=admin_session_id,
            )
        },
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200


def test_refresh_rotates_cookie_and_returns_no_refresh_token(auth_environment):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    user_id = _create_user(factory)
    session_id, old_token = _create_session(factory, user_id)
    csrf_token = uuid.uuid4().hex

    response = client.post(
        "/api/auth/refresh",
        headers=_csrf_headers(csrf_token),
        cookies={
            settings.AUTH_REFRESH_COOKIE_NAME: old_token,
            settings.AUTH_CSRF_COOKIE_NAME: csrf_token,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "access_token",
        "token_type",
        "expires_in",
        "csrf_token",
    }
    assert old_token not in response.text
    new_token = response.cookies[settings.AUTH_REFRESH_COOKIE_NAME]
    assert new_token != old_token
    claims = verify_access_token(body["access_token"])
    assert claims.user_id == user_id
    assert claims.session_id == session_id
    assert response.headers["Cache-Control"] == "no-store"

    with factory() as db:
        auth_session = db.get(AuthSessionModel, session_id)
        history = db.scalar(select(AuthRefreshTokenHistoryModel))
    assert auth_session.token_hash == hash_refresh_token(new_token)
    assert history.token_hash == hash_refresh_token(old_token)


def test_refresh_rejects_bad_csrf_and_untrusted_origin(auth_environment):
    client = auth_environment["client"]
    token = generate_refresh_token()
    bad_csrf = client.post(
        "/api/auth/refresh",
        headers={
            **_origin_headers(),
            settings.AUTH_CSRF_HEADER_NAME: "mismatch",
        },
        cookies={
            settings.AUTH_REFRESH_COOKIE_NAME: token,
            settings.AUTH_CSRF_COOKIE_NAME: "different",
        },
    )
    bad_origin = client.post(
        "/api/auth/refresh",
        headers={settings.AUTH_CSRF_HEADER_NAME: "csrf"},
        cookies={
            settings.AUTH_REFRESH_COOKIE_NAME: token,
            settings.AUTH_CSRF_COOKIE_NAME: "csrf",
        },
    )
    assert bad_csrf.status_code == 403
    assert bad_origin.status_code == 403


def test_invalid_refresh_clears_auth_cookies(auth_environment):
    response = auth_environment["client"].post(
        "/api/auth/refresh",
        headers=_csrf_headers("csrf-value"),
        cookies={
            settings.AUTH_REFRESH_COOKIE_NAME: generate_refresh_token(),
            settings.AUTH_CSRF_COOKIE_NAME: "csrf-value",
        },
    )
    assert response.status_code == 401
    assert settings.AUTH_REFRESH_COOKIE_NAME in response.headers.get(
        "set-cookie",
        "",
    )
    assert response.headers["Cache-Control"] == "no-store"


def test_refresh_signing_configuration_fails_before_rotating_token(
    auth_environment,
    monkeypatch,
):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    user_id = _create_user(factory)
    session_id, raw_token = _create_session(factory, user_id)
    monkeypatch.setattr(settings, "AUTH_JWT_SECRET_KEY", "")

    response = client.post(
        "/api/auth/refresh",
        headers=_csrf_headers("csrf-value"),
        cookies={
            settings.AUTH_REFRESH_COOKIE_NAME: raw_token,
            settings.AUTH_CSRF_COOKIE_NAME: "csrf-value",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Authentication service is unavailable."
    }
    with factory() as db:
        auth_session = db.get(AuthSessionModel, session_id)
    assert auth_session.token_hash == hash_refresh_token(raw_token)


def test_logout_revokes_current_session_and_clears_cookies(auth_environment):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    user_id = _create_user(factory)
    session_id, _ = _create_session(factory, user_id)
    access_token = create_access_token(user_id=user_id, session_id=session_id)

    response = client.post(
        "/api/auth/logout",
        headers={
            **_csrf_headers("csrf-value"),
            "Authorization": f"Bearer {access_token}",
        },
        cookies=_csrf_cookies("csrf-value"),
    )

    assert response.status_code == 200
    with factory() as db:
        auth_session = db.get(AuthSessionModel, session_id)
    assert auth_session.revoked_at is not None
    assert response.json() == {"status": "logged_out"}

    repeat = client.post(
        "/api/auth/logout",
        headers={
            **_csrf_headers("csrf-value"),
            "Authorization": f"Bearer {access_token}",
        },
        cookies=_csrf_cookies("csrf-value"),
    )
    assert repeat.status_code == 200
    assert repeat.json() == {"status": "logged_out"}


def test_logout_all_revokes_all_user_sessions(auth_environment):
    client = auth_environment["client"]
    factory = auth_environment["factory"]
    user_id = _create_user(factory)
    session_ids = {
        _create_session(factory, user_id)[0],
        _create_session(factory, user_id)[0],
    }
    current_session_id = next(iter(session_ids))
    access_token = create_access_token(
        user_id=user_id,
        session_id=current_session_id,
    )

    response = client.post(
        "/api/auth/logout-all",
        headers={
            **_csrf_headers("csrf-value"),
            "Authorization": f"Bearer {access_token}",
        },
        cookies=_csrf_cookies("csrf-value"),
    )

    assert response.status_code == 200
    with factory() as db:
        sessions = db.scalars(
            select(AuthSessionModel).where(
                AuthSessionModel.id.in_(session_ids)
            )
        ).all()
    assert len(sessions) == 2
    assert all(session.revoked_at is not None for session in sessions)


def test_auth_middleware_rejects_oversized_body_and_sets_no_store(
    auth_environment,
):
    response = auth_environment["client"].post(
        "/api/auth/login",
        content=b"x" * (auth_api.AUTH_BODY_MAX_BYTES + 1),
        headers={"Content-Type": "application/json", **_origin_headers()},
    )
    assert response.status_code == 413
    assert response.headers["Cache-Control"] == "no-store"


def test_database_errors_return_generic_response_without_details(
    auth_environment,
    caplog,
):
    engine = auth_environment["factory"].kw["bind"]

    def fail_query(_conn, _cursor, _statement, _parameters, _context, _many):
        raise SQLAlchemyError("sensitive database diagnostic")

    event.listen(engine, "before_cursor_execute", fail_query)
    try:
        response = auth_environment["client"].post(
            "/api/auth/login",
            json={
                "email": "person@example.test",
                "password": "correct horse battery staple",
            },
            headers=_origin_headers(),
        )
    finally:
        event.remove(engine, "before_cursor_execute", fail_query)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Authentication service is unavailable."
    }
    assert "sensitive database diagnostic" not in response.text
    assert "sensitive database diagnostic" not in caplog.text
