"""Database-backed refresh-token rotation.

The caller must provide a clean SQLAlchemy session; this service owns and
commits the rotation transaction.  Lock order is session, user, then token
history.  Other authentication operations that lock these rows must use the
same order.  MySQL/InnoDB row-lock behavior requires separate integration
testing; SQLite ignores SELECT FOR UPDATE.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterator

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .auth_models import (
    AuditLogModel,
    AuthRefreshTokenHistoryModel,
    AuthSessionModel,
    UserModel,
)
from .security import generate_refresh_token, hash_refresh_token


class InvalidRefreshTokenError(ValueError):
    """Raised for invalid, expired, revoked, or reused refresh credentials."""


_INVALID_REFRESH_TOKEN_MESSAGE = "Refresh token is invalid."
_MAX_REFRESH_TOKEN_BYTES = 256


class RefreshServiceUnavailableError(RuntimeError):
    """Raised without database diagnostics when refresh storage fails."""


@contextmanager
def _rotation_transaction(db: Session) -> Iterator[None]:
    try:
        with db.begin():
            yield
    except SQLAlchemyError:
        # Database exceptions can include SQL parameters.  Do not chain them
        # into errors that an API handler or logger might expose.
        raise RefreshServiceUnavailableError(
            "Refresh service is unavailable."
        ) from None


@dataclass(frozen=True)
class RefreshTokenRotation:
    """Return a raw token only after its hash commits successfully."""

    session_id: str
    user_id: str
    expires_at: datetime
    token: str = field(repr=False)


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidRefreshTokenError(_INVALID_REFRESH_TOKEN_MESSAGE)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _session_lock_statement(session_id: str):
    return (
        select(AuthSessionModel)
        .where(AuthSessionModel.id == session_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def _user_lock_statement(user_id: str):
    return (
        select(UserModel)
        .where(UserModel.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def _history_lock_statement(token_hash: str):
    return (
        select(AuthRefreshTokenHistoryModel)
        .where(AuthRefreshTokenHistoryModel.token_hash == token_hash)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def rotate_refresh_token(
    db: Session,
    raw_token: str,
    *,
    token_lifetime: timedelta,
    now: datetime | None = None,
) -> RefreshTokenRotation:
    """Consume a current token and atomically persist its replacement hash.

    ``token_lifetime`` is explicit because the application has not yet chosen
    a refresh-token lifetime setting.  ``AuthSessionModel.expires_at`` remains
    the absolute session expiry and is never extended here.
    """
    if db.in_transaction():
        raise RuntimeError(
            "Refresh rotation requires a clean database session."
        )
    if not isinstance(raw_token, str) or not raw_token:
        raise InvalidRefreshTokenError(_INVALID_REFRESH_TOKEN_MESSAGE)
    try:
        encoded_token = raw_token.encode("ascii")
    except UnicodeEncodeError:
        raise InvalidRefreshTokenError(
            _INVALID_REFRESH_TOKEN_MESSAGE
        ) from None
    if len(encoded_token) > _MAX_REFRESH_TOKEN_BYTES:
        raise InvalidRefreshTokenError(_INVALID_REFRESH_TOKEN_MESSAGE)
    if (
        not isinstance(token_lifetime, timedelta)
        or token_lifetime <= timedelta(0)
    ):
        raise ValueError("A positive refresh-token lifetime is required.")

    token_hash = hash_refresh_token(raw_token)
    current_time = _as_utc(now or datetime.now(timezone.utc))
    rotation: RefreshTokenRotation | None = None
    reuse_detected = False

    with _rotation_transaction(db):
        # These locator reads acquire no row locks.  Once the owning session is
        # known, all row locks follow session -> user -> history order.
        session_id = db.scalar(
            select(AuthSessionModel.id).where(
                AuthSessionModel.token_hash == token_hash
            )
        )
        if session_id is None:
            session_id = db.scalar(
                select(AuthRefreshTokenHistoryModel.session_id).where(
                    AuthRefreshTokenHistoryModel.token_hash == token_hash
                )
            )
        if session_id is None:
            raise InvalidRefreshTokenError(_INVALID_REFRESH_TOKEN_MESSAGE)

        auth_session = db.scalar(_session_lock_statement(session_id))
        if auth_session is None:
            raise InvalidRefreshTokenError(_INVALID_REFRESH_TOKEN_MESSAGE)

        user = db.scalar(_user_lock_statement(auth_session.user_id))
        if user is None:
            raise InvalidRefreshTokenError(_INVALID_REFRESH_TOKEN_MESSAGE)

        if auth_session.token_hash == token_hash:
            if (
                not user.is_active
                or auth_session.revoked_at is not None
                or current_time >= _as_utc(auth_session.expires_at)
                or current_time
                >= _as_utc(auth_session.current_refresh_expires_at)
            ):
                raise InvalidRefreshTokenError(_INVALID_REFRESH_TOKEN_MESSAGE)

            next_token_expiry = min(
                current_time + token_lifetime,
                _as_utc(auth_session.expires_at),
            )
            next_raw_token = generate_refresh_token()
            next_token_hash = hash_refresh_token(next_raw_token)

            db.add(
                AuthRefreshTokenHistoryModel(
                    token_hash=token_hash,
                    session_id=auth_session.id,
                    expires_at=_as_utc(
                        auth_session.current_refresh_expires_at
                    ),
                    consumed_at=current_time,
                )
            )
            auth_session.token_hash = next_token_hash
            auth_session.current_refresh_expires_at = next_token_expiry
            auth_session.last_used_at = current_time
            rotation = RefreshTokenRotation(
                session_id=auth_session.id,
                user_id=user.id,
                expires_at=next_token_expiry,
                token=next_raw_token,
            )
        else:
            history_entry = db.scalar(_history_lock_statement(token_hash))
            if (
                history_entry is None
                or history_entry.session_id != auth_session.id
            ):
                raise InvalidRefreshTokenError(_INVALID_REFRESH_TOKEN_MESSAGE)

            if auth_session.revoked_at is None:
                auth_session.revoked_at = current_time
                db.add(
                    AuditLogModel(
                        actor_user_id=auth_session.user_id,
                        action="refresh_token_reuse_detected",
                        target_type="auth_session",
                        target_id=auth_session.id,
                        occurred_at=current_time,
                    )
                )
            reuse_detected = True

    # Reuse revocation must commit before reporting failure to the caller.
    if reuse_detected:
        raise InvalidRefreshTokenError(_INVALID_REFRESH_TOKEN_MESSAGE)
    if rotation is None:
        raise InvalidRefreshTokenError(_INVALID_REFRESH_TOKEN_MESSAGE)
    return rotation
