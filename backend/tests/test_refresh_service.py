"""Isolated refresh-service tests; no app startup or live database imports."""

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy import Column, String, Table, create_engine, event, select
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.auth_models import (
    AuditLogModel,
    AuthRefreshTokenHistoryModel,
    AuthSessionModel,
    UserModel,
)
from app.database import Base
from app.security import generate_refresh_token, hash_refresh_token
from app.auth_service import (
    InvalidRefreshTokenError,
    RefreshServiceUnavailableError,
    _history_lock_statement,
    _session_lock_statement,
    _user_lock_statement,
    rotate_refresh_token,
)


TEST_NOW = datetime(2035, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def session_factory():
    if "employees" not in Base.metadata.tables:
        Table(
            "employees",
            Base.metadata,
            Column("id", String(50), primary_key=True),
        )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _create_session(
    session_factory,
    *,
    now=TEST_NOW,
    active=True,
    token_expires_at=None,
    session_expires_at=None,
    revoked_at=None,
):
    initial_token = generate_refresh_token()
    absolute_expiry = session_expires_at or now + timedelta(hours=2)
    current_token_expiry = token_expires_at or now + timedelta(minutes=20)

    with session_factory.begin() as db:
        user = UserModel(
            email=f"user-{uuid.uuid4().hex}@example.test",
            password_hash="test-only-hash",
            is_active=active,
        )
        db.add(user)
        db.flush()
        auth_session = AuthSessionModel(
            user_id=user.id,
            token_hash=hash_refresh_token(initial_token),
            issued_at=now,
            expires_at=absolute_expiry,
            current_refresh_expires_at=current_token_expiry,
            revoked_at=revoked_at,
        )
        db.add(auth_session)
        db.flush()
        session_id = auth_session.id
        user_id = user.id

    return initial_token, session_id, user_id, absolute_expiry


def test_rotation_persists_hash_only_and_keeps_absolute_expiry(
    session_factory,
):
    raw_token, session_id, _, absolute_expiry = _create_session(
        session_factory
    )

    with session_factory() as db:
        result = rotate_refresh_token(
            db,
            raw_token,
            token_lifetime=timedelta(hours=1),
            now=TEST_NOW,
        )

    assert result.session_id == session_id
    assert result.expires_at == TEST_NOW + timedelta(hours=1)
    assert raw_token not in repr(result)

    with session_factory() as db:
        auth_session = db.get(AuthSessionModel, session_id)
        history = db.scalar(select(AuthRefreshTokenHistoryModel))

    assert auth_session.token_hash == hash_refresh_token(result.token)
    assert (
        auth_session.expires_at.replace(tzinfo=timezone.utc)
        == absolute_expiry
    )
    assert (
        auth_session.current_refresh_expires_at.replace(tzinfo=timezone.utc)
        == result.expires_at
    )
    assert history.token_hash == hash_refresh_token(raw_token)
    assert history.token_hash != raw_token
    assert history.session_id == session_id
    assert history.consumed_at.replace(tzinfo=timezone.utc) == TEST_NOW


def test_reuse_after_multiple_rotations_revokes_only_own_session(
    session_factory,
):
    first_token, session_id, _, _ = _create_session(session_factory)
    unrelated_token, unrelated_session_id, _, _ = _create_session(
        session_factory
    )
    with session_factory() as db:
        second_rotation = rotate_refresh_token(
            db,
            first_token,
            token_lifetime=timedelta(hours=1),
            now=TEST_NOW,
        )
    with session_factory() as db:
        third_rotation = rotate_refresh_token(
            db,
            second_rotation.token,
            token_lifetime=timedelta(hours=1),
            now=TEST_NOW + timedelta(minutes=1),
        )

    with session_factory() as db:
        with pytest.raises(
            InvalidRefreshTokenError,
            match="^Refresh token is invalid\\.$",
        ):
            rotate_refresh_token(
                db,
                first_token,
                token_lifetime=timedelta(hours=1),
                now=TEST_NOW + timedelta(minutes=2),
            )

    with session_factory() as db:
        auth_session = db.get(AuthSessionModel, session_id)
        unrelated_session = db.get(AuthSessionModel, unrelated_session_id)
        history_hashes = set(
            db.scalars(select(AuthRefreshTokenHistoryModel.token_hash)).all()
        )
        audit_event = db.scalar(select(AuditLogModel))

    assert (
        auth_session.revoked_at.replace(tzinfo=timezone.utc)
        == TEST_NOW + timedelta(minutes=2)
    )
    assert auth_session.token_hash == hash_refresh_token(third_rotation.token)
    assert unrelated_session.revoked_at is None
    assert unrelated_session.token_hash == hash_refresh_token(unrelated_token)
    assert history_hashes == {
        hash_refresh_token(first_token),
        hash_refresh_token(second_rotation.token),
    }
    assert audit_event.action == "refresh_token_reuse_detected"
    assert audit_event.target_id == session_id
    assert first_token not in audit_event.action
    assert hash_refresh_token(first_token) not in audit_event.target_id


def test_unknown_token_does_not_revoke_an_unrelated_session(session_factory):
    _, session_id, _, _ = _create_session(session_factory)

    with session_factory() as db:
        with pytest.raises(InvalidRefreshTokenError):
            rotate_refresh_token(
                db,
                generate_refresh_token(),
                token_lifetime=timedelta(hours=1),
                now=TEST_NOW,
            )

    with session_factory() as db:
        auth_session = db.get(AuthSessionModel, session_id)
        audit_count = len(db.scalars(select(AuditLogModel.id)).all())

    assert auth_session.revoked_at is None
    assert audit_count == 0


@pytest.mark.parametrize(
    ("session_options", "failure_time"),
    [
        ({"token_expires_at": TEST_NOW - timedelta(seconds=1)}, TEST_NOW),
        ({"session_expires_at": TEST_NOW - timedelta(seconds=1)}, TEST_NOW),
        ({"revoked_at": TEST_NOW - timedelta(seconds=1)}, TEST_NOW),
        ({"active": False}, TEST_NOW),
    ],
    ids=[
        "expired-token",
        "expired-session",
        "revoked-session",
        "inactive-user",
    ],
)
def test_invalid_session_state_rejects_current_token(
    session_factory,
    session_options,
    failure_time,
):
    raw_token, _, _, _ = _create_session(session_factory, **session_options)

    with session_factory() as db:
        with pytest.raises(InvalidRefreshTokenError):
            rotate_refresh_token(
                db,
                raw_token,
                token_lifetime=timedelta(hours=1),
                now=failure_time,
            )


@pytest.mark.parametrize("changed_state", ["session", "user"])
def test_locked_reads_refresh_preloaded_identity_state(
    session_factory,
    changed_state,
):
    raw_token, session_id, user_id, _ = _create_session(session_factory)

    with session_factory() as stale_db:
        stale_session = stale_db.get(AuthSessionModel, session_id)
        stale_user = stale_db.get(UserModel, user_id)
        assert stale_session.revoked_at is None
        assert stale_user.is_active is True
        stale_db.commit()

        with session_factory.begin() as updater:
            if changed_state == "session":
                updater.get(AuthSessionModel, session_id).revoked_at = TEST_NOW
            else:
                updater.get(UserModel, user_id).is_active = False

        with pytest.raises(InvalidRefreshTokenError):
            rotate_refresh_token(
                stale_db,
                raw_token,
                token_lifetime=timedelta(hours=1),
                now=TEST_NOW,
            )

    with session_factory() as db:
        auth_session = db.get(AuthSessionModel, session_id)
        user = db.get(UserModel, user_id)

    assert auth_session.token_hash == hash_refresh_token(raw_token)
    if changed_state == "session":
        assert auth_session.revoked_at.replace(tzinfo=timezone.utc) == TEST_NOW
    else:
        assert user.is_active is False


@pytest.mark.parametrize(
    "expiry_field",
    ["expires_at", "current_refresh_expires_at"],
)
def test_malformed_expiry_values_reject_without_rotation(
    session_factory,
    expiry_field,
):
    raw_token, session_id, _, _ = _create_session(session_factory)

    def corrupt_expiry(_session, instance):
        if isinstance(instance, AuthSessionModel):
            setattr(instance, expiry_field, None)

    event.listen(Session, "loaded_as_persistent", corrupt_expiry)
    try:
        with session_factory() as db:
            with pytest.raises(InvalidRefreshTokenError):
                rotate_refresh_token(
                    db,
                    raw_token,
                    token_lifetime=timedelta(hours=1),
                    now=TEST_NOW,
                )
    finally:
        event.remove(Session, "loaded_as_persistent", corrupt_expiry)

    with session_factory() as db:
        auth_session = db.get(AuthSessionModel, session_id)

    assert auth_session.token_hash == hash_refresh_token(raw_token)
    assert auth_session.revoked_at is None


@pytest.mark.parametrize("raw_token", ["x" * 257, "\u00e9"])
def test_oversized_or_non_ascii_token_is_rejected_before_database_use(
    session_factory,
    raw_token,
):
    with session_factory() as db:
        with pytest.raises(InvalidRefreshTokenError):
            rotate_refresh_token(
                db,
                raw_token,
                token_lifetime=timedelta(hours=1),
                now=TEST_NOW,
            )

        assert db.in_transaction() is False


def test_audit_insert_failure_rolls_back_reuse_revocation(
    session_factory,
    caplog,
):
    consumed_token, session_id, _, _ = _create_session(session_factory)
    with session_factory() as db:
        current_rotation = rotate_refresh_token(
            db,
            consumed_token,
            token_lifetime=timedelta(hours=1),
            now=TEST_NOW,
        )

    def fail_audit_insert(_mapper, _connection, _target):
        raise SQLAlchemyError("injected audit storage failure")

    event.listen(AuditLogModel, "before_insert", fail_audit_insert)
    try:
        with session_factory() as db:
            with pytest.raises(RefreshServiceUnavailableError) as failure:
                rotate_refresh_token(
                    db,
                    consumed_token,
                    token_lifetime=timedelta(hours=1),
                    now=TEST_NOW + timedelta(minutes=1),
                )
    finally:
        event.remove(AuditLogModel, "before_insert", fail_audit_insert)

    assert str(failure.value) == "Refresh service is unavailable."
    assert failure.value.__suppress_context__ is True
    assert consumed_token not in caplog.text
    assert hash_refresh_token(consumed_token) not in caplog.text

    with session_factory() as db:
        auth_session = db.get(AuthSessionModel, session_id)
        history_hashes = set(
            db.scalars(select(AuthRefreshTokenHistoryModel.token_hash)).all()
        )
        audit_count = len(db.scalars(select(AuditLogModel.id)).all())

    assert auth_session.revoked_at is None
    assert (
        auth_session.token_hash
        == hash_refresh_token(current_rotation.token)
    )
    assert history_hashes == {hash_refresh_token(consumed_token)}
    assert audit_count == 0


def test_commit_failure_rolls_back_rotation_and_returns_no_new_token(
    session_factory,
):
    raw_token, session_id, _, _ = _create_session(session_factory)

    with session_factory() as db:
        def fail_before_commit(_session):
            raise RuntimeError("injected commit failure")

        from sqlalchemy import event

        event.listen(db, "before_commit", fail_before_commit)
        try:
            with pytest.raises(RuntimeError, match="injected commit failure"):
                rotate_refresh_token(
                    db,
                    raw_token,
                    token_lifetime=timedelta(hours=1),
                    now=TEST_NOW,
                )
        finally:
            event.remove(db, "before_commit", fail_before_commit)

    with session_factory() as db:
        auth_session = db.get(AuthSessionModel, session_id)
        history_count = len(
            db.scalars(select(AuthRefreshTokenHistoryModel.token_hash)).all()
        )

    assert auth_session.token_hash == hash_refresh_token(raw_token)
    assert history_count == 0


def test_lock_statements_compile_to_mysql_for_update():
    statements = (
        _session_lock_statement("ses-test"),
        _user_lock_statement("usr-test"),
        _history_lock_statement("0" * 64),
    )

    assert all(
        "FOR UPDATE" in str(statement.compile(dialect=mysql.dialect())).upper()
        for statement in statements
    )
