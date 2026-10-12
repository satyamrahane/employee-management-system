"""Unit tests for auth primitives; they intentionally do not import app.main or a database."""

from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("jwt")
pytest.importorskip("pwdlib")

import jwt

from app import security


TEST_JWT_SECRET = "test-only-jwt-signing-secret-with-at-least-thirty-two-bytes"


@pytest.fixture(autouse=True)
def configured_auth_settings(monkeypatch):
    monkeypatch.setattr(security.settings, "AUTH_JWT_SECRET_KEY", TEST_JWT_SECRET)
    monkeypatch.setattr(security.settings, "AUTH_JWT_ISSUER", "ems-test-api")
    monkeypatch.setattr(security.settings, "AUTH_JWT_AUDIENCE", "ems-test-client")
    monkeypatch.setattr(security.settings, "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", 15)
    monkeypatch.setattr(security.settings, "AUTH_MIN_PASSWORD_LENGTH", 12)
    monkeypatch.setattr(security.settings, "AUTH_MAX_PASSWORD_LENGTH", 128)


def test_password_hashing_and_verification():
    password_hash = security.hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert password_hash.startswith("$argon2")
    assert security.verify_password("correct horse battery staple", password_hash) is True
    assert security.verify_password("incorrect password", password_hash) is False


def test_password_policy_rejects_short_or_blank_passwords():
    with pytest.raises(security.PasswordValidationError):
        security.hash_password("short")
    with pytest.raises(security.PasswordValidationError):
        security.hash_password(" " * 12)


def test_access_token_round_trip_contains_only_required_identity_claims():
    token = security.create_access_token(user_id="usr-test", session_id="ses-test")
    claims = security.verify_access_token(token)

    assert claims.user_id == "usr-test"
    assert claims.session_id == "ses-test"
    assert claims.expires_at > claims.issued_at


def test_expired_access_token_is_rejected():
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {
            "sub": "usr-test",
            "sid": "ses-test",
            "iss": "ems-test-api",
            "aud": "ems-test-client",
            "iat": now - timedelta(minutes=2),
            "nbf": now - timedelta(minutes=2),
            "exp": now - timedelta(minutes=1),
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )

    with pytest.raises(security.InvalidAccessTokenError):
        security.verify_access_token(expired_token)


def test_access_token_signed_with_different_key_is_rejected():
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "usr-test",
            "sid": "ses-test",
            "iss": "ems-test-api",
            "aud": "ems-test-client",
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=5),
        },
        "different-test-signing-key-with-more-than-thirty-two-bytes",
        algorithm="HS256",
    )

    with pytest.raises(security.InvalidAccessTokenError):
        security.verify_access_token(token)


@pytest.mark.parametrize(
    ("issuer", "audience"),
    [("wrong-issuer", "ems-test-client"), ("ems-test-api", "wrong-audience")],
)
def test_wrong_issuer_or_audience_is_rejected(issuer, audience):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "usr-test",
            "sid": "ses-test",
            "iss": issuer,
            "aud": audience,
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=5),
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )

    with pytest.raises(security.InvalidAccessTokenError):
        security.verify_access_token(token)


def test_missing_or_insecure_jwt_secret_fails_safely(monkeypatch):
    monkeypatch.setattr(security.settings, "AUTH_JWT_SECRET_KEY", "change-me")

    with pytest.raises(security.SecurityConfigurationError):
        security.create_access_token(user_id="usr-test", session_id="ses-test")


def test_long_repeated_character_jwt_secret_is_rejected(monkeypatch):
    monkeypatch.setattr(security.settings, "AUTH_JWT_SECRET_KEY", "a" * 64)

    with pytest.raises(security.SecurityConfigurationError):
        security.create_access_token(user_id="usr-test", session_id="ses-test")


def test_refresh_tokens_are_random_and_only_hashes_are_deterministic():
    first = security.generate_refresh_token()
    second = security.generate_refresh_token()

    assert first != second
    assert len(first) >= 64
    assert security.hash_refresh_token(first) == security.hash_refresh_token(first)
    assert security.hash_refresh_token(first) != security.hash_refresh_token(second)
