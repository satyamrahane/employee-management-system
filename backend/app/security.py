"""Authentication cryptographic primitives.

This module deliberately contains no routes, database access, token logging,
or configuration output.  The future authentication service is responsible for
storing only the hashes returned here and for enforcing session/token lifecycle
rules against the migration-controlled authentication tables.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any, Mapping

import jwt
from jwt import InvalidTokenError as PyJWTInvalidTokenError
from pwdlib import PasswordHash

from .config import settings


_PASSWORD_HASHER = PasswordHash.recommended()
_MIN_JWT_SECRET_BYTES = 32
_INSECURE_JWT_SECRETS = frozenset(
    {
        "change-me",
        "changeme",
        "default",
        "secret",
        "test",
        "your-secret-key",
    }
)


class SecurityConfigurationError(RuntimeError):
    """Raised when required authentication configuration is absent or unsafe."""


class PasswordValidationError(ValueError):
    """Raised when a proposed password does not meet the local policy."""


class InvalidAccessTokenError(ValueError):
    """Raised for expired, malformed, improperly signed, or invalid JWTs."""


@dataclass(frozen=True)
class AccessTokenClaims:
    """The only application claims accepted from a verified access token."""

    user_id: str
    session_id: str
    issued_at: datetime
    expires_at: datetime


def password_validation_errors(password: str) -> list[str]:
    """Return user-safe password policy failures without retaining the secret."""
    if not isinstance(password, str):
        return ["Password must be text."]

    errors: list[str] = []
    if len(password) < settings.AUTH_MIN_PASSWORD_LENGTH:
        errors.append(
            f"Password must be at least {settings.AUTH_MIN_PASSWORD_LENGTH} characters long."
        )
    if len(password) > settings.AUTH_MAX_PASSWORD_LENGTH:
        errors.append(
            f"Password must be no more than {settings.AUTH_MAX_PASSWORD_LENGTH} characters long."
        )
    if not password.strip():
        errors.append("Password cannot be blank.")
    return errors


def validate_password(password: str) -> None:
    """Raise a policy error instead of ever returning or logging a password."""
    errors = password_validation_errors(password)
    if errors:
        raise PasswordValidationError(" ".join(errors))


def hash_password(password: str) -> str:
    """Validate and hash a password with pwdlib's recommended Argon2id settings."""
    validate_password(password)
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a password matches a stored Argon2id hash."""
    if not isinstance(password, str) or not isinstance(password_hash, str) or not password_hash:
        return False
    try:
        return _PASSWORD_HASHER.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """Report whether a valid stored hash should be upgraded after successful login."""
    if not isinstance(password_hash, str) or not password_hash:
        return True
    try:
        return _PASSWORD_HASHER.needs_rehash(password_hash)
    except (ValueError, TypeError):
        return True


def _validated_jwt_secret() -> str:
    """Reject weak patterns; deployments must use a
    cryptographically secure random generator.

    These pattern checks are heuristics and cannot establish cryptographic
    randomness or entropy.
    """
    secret = settings.AUTH_JWT_SECRET_KEY
    if not isinstance(secret, str):
        raise SecurityConfigurationError("JWT signing configuration is invalid.")

    normalized = secret.strip()
    normalized_lower = normalized.lower()
    has_short_repeating_pattern = any(
        all(
            normalized_lower[index] == normalized_lower[index % period]
            for index in range(period, len(normalized_lower))
        )
        for period in range(1, min(9, len(normalized_lower)))
    )
    if (
        len(normalized.encode("utf-8")) < _MIN_JWT_SECRET_BYTES
        or normalized_lower in _INSECURE_JWT_SECRETS
        or len(set(normalized_lower)) < 4
        or has_short_repeating_pattern
    ):
        raise SecurityConfigurationError("JWT signing configuration is missing or insecure.")
    return secret


def _validated_token_configuration() -> tuple[str, str, str, timedelta]:
    secret = _validated_jwt_secret()
    issuer = settings.AUTH_JWT_ISSUER.strip()
    audience = settings.AUTH_JWT_AUDIENCE.strip()
    lifetime = timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
    if not issuer or not audience or lifetime <= timedelta(0):
        raise SecurityConfigurationError("JWT issuer, audience, or lifetime is invalid.")
    return secret, issuer, audience, lifetime


def validate_access_token_configuration() -> None:
    """Fail before state changes if access-token signing is not configured."""
    _validated_token_configuration()


def create_access_token(*, user_id: str, session_id: str) -> str:
    """Create a short-lived signed JWT with no personally identifiable claims."""
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("A non-empty user ID is required.")
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("A non-empty session ID is required.")

    secret, issuer, audience, lifetime = _validated_token_configuration()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "sid": session_id,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "nbf": now,
        "exp": now + lifetime,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, secret, algorithm=settings.AUTH_JWT_ALGORITHM)


def verify_access_token(token: str) -> AccessTokenClaims:
    """Verify signature, expiry, issuer, audience, and required token claims."""
    if not isinstance(token, str) or not token:
        raise InvalidAccessTokenError("Access token is invalid.")

    secret, issuer, audience, _ = _validated_token_configuration()
    try:
        payload: Mapping[str, Any] = jwt.decode(
            token,
            secret,
            algorithms=[settings.AUTH_JWT_ALGORITHM],
            issuer=issuer,
            audience=audience,
            options={"require": ["sub", "sid", "iss", "aud", "iat", "nbf", "exp"]},
        )
    except PyJWTInvalidTokenError as exc:
        raise InvalidAccessTokenError("Access token is invalid or expired.") from exc

    user_id = payload.get("sub")
    session_id = payload.get("sid")
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    if (
        not isinstance(user_id, str)
        or not user_id
        or not isinstance(session_id, str)
        or not session_id
        or not isinstance(issued_at, (int, float))
        or not isinstance(expires_at, (int, float))
    ):
        raise InvalidAccessTokenError("Access token claims are invalid.")

    return AccessTokenClaims(
        user_id=user_id,
        session_id=session_id,
        issued_at=datetime.fromtimestamp(issued_at, tz=timezone.utc),
        expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc),
    )


def generate_refresh_token() -> str:
    """Generate a high-entropy opaque token suitable for server-side hashing."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Return a deterministic SHA-256 digest for lookup/storage of an opaque token."""
    if not isinstance(token, str) or not token:
        raise ValueError("A non-empty refresh token is required.")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
