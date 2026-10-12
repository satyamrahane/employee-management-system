"""SQLAlchemy models for authentication and authorization.

These mappings intentionally live outside ``app.models`` and are not imported
by the employee application while authentication remains unmounted. Alembic
imports this module explicitly when assembling Base.metadata.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)

from .database import Base


def _prefixed_uuid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def generate_user_id() -> str:
    return _prefixed_uuid("usr")


def generate_role_id() -> str:
    return _prefixed_uuid("role")


def generate_session_id() -> str:
    return _prefixed_uuid("ses")


def generate_reset_token_id() -> str:
    return _prefixed_uuid("rst")


def generate_audit_event_id() -> str:
    return _prefixed_uuid("aud")


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, default=generate_user_id)
    email = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    failed_login_count = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    employee_id = Column(
        String(50),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class RoleModel(Base):
    __tablename__ = "roles"

    id = Column(String(50), primary_key=True, default=generate_role_id)
    name = Column(String(32), nullable=False, unique=True, index=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class UserRoleModel(Base):
    __tablename__ = "user_roles"

    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(String(50), ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True)
    assigned_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class AuthSessionModel(Base):
    __tablename__ = "auth_sessions"

    id = Column(String(50), primary_key=True, default=generate_session_id)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    issued_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    current_refresh_expires_at = Column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    device_label = Column(String(255), nullable=True)


class AuthRefreshTokenHistoryModel(Base):
    __tablename__ = "auth_refresh_token_history"
    __table_args__ = (
        Index(
            "ix_auth_refresh_token_history_session_id_expires_at",
            "session_id",
            "expires_at",
        ),
        Index("ix_auth_refresh_token_history_expires_at", "expires_at"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    token_hash = Column(String(64), primary_key=True)
    session_id = Column(
        String(50),
        ForeignKey(
            "auth_sessions.id",
            name="fk_auth_refresh_token_history_session_id_auth_sessions",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=False)


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(50), primary_key=True, default=generate_reset_token_id)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True, index=True)


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id = Column(String(50), primary_key=True, default=generate_audit_event_id)
    actor_user_id = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    target_type = Column(String(100), nullable=True)
    target_id = Column(String(50), nullable=True)
    correlation_id = Column(String(100), nullable=True, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
