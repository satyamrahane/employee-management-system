"""Add authentication and authorization schema.

Revision ID: 20261011_0002
Revises: 20261011_0001
Create Date: 2026-10-11

This additive revision creates only authentication-related tables.  It never
creates, alters, or copies the existing employees table or its records.
Passwords and opaque refresh/reset tokens are represented only by hashes; no
plaintext secret is persisted.  MySQL table options match the verified EMS
employees baseline.
"""

from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261011_0002"
down_revision: Union[str, Sequence[str], None] = "20261011_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MYSQL_TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        **MYSQL_TABLE_OPTIONS,
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)
    # Roles are policy data, not accounts.  No administrator user or password
    # is seeded by this migration.
    # MySQL DATETIME is timezone-naive; persist the UTC wall-clock value.
    role_created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.String(length=50)),
        sa.column("name", sa.String(length=32)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        roles_table,
        [
            {
                "id": "role-admin",
                "name": "ADMIN",
                "created_at": role_created_at,
            },
            {
                "id": "role-hr",
                "name": "HR",
                "created_at": role_created_at,
            },
        ],
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("employee_id", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], name="fk_users_employee_id_employees", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        **MYSQL_TABLE_OPTIONS,
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_employee_id", "users", ["employee_id"], unique=True)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("role_id", sa.String(length=50), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name="fk_user_roles_role_id_roles", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_roles_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
        **MYSQL_TABLE_OPTIONS,
    )
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_label", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_auth_sessions_user_id_users", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        **MYSQL_TABLE_OPTIONS,
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"], unique=False)
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"], unique=False)
    op.create_index("ix_auth_sessions_revoked_at", "auth_sessions", ["revoked_at"], unique=False)

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_password_reset_tokens_user_id_users", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        **MYSQL_TABLE_OPTIONS,
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"], unique=False)
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)
    op.create_index("ix_password_reset_tokens_expires_at", "password_reset_tokens", ["expires_at"], unique=False)
    op.create_index("ix_password_reset_tokens_consumed_at", "password_reset_tokens", ["consumed_at"], unique=False)

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("actor_user_id", sa.String(length=50), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.String(length=50), nullable=True),
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_audit_log_actor_user_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        **MYSQL_TABLE_OPTIONS,
    )
    op.create_index("ix_audit_log_actor_user_id", "audit_log", ["actor_user_id"], unique=False)
    op.create_index("ix_audit_log_action", "audit_log", ["action"], unique=False)
    op.create_index("ix_audit_log_correlation_id", "audit_log", ["correlation_id"], unique=False)
    op.create_index("ix_audit_log_occurred_at", "audit_log", ["occurred_at"], unique=False)


def downgrade() -> None:
    # This removes only tables introduced by this revision; employees is never
    # referenced by a destructive operation.  Do not use this downgrade on a
    # database that contains authentication data unless its data-loss impact is
    # explicitly approved.
    op.drop_index("ix_audit_log_occurred_at", table_name="audit_log")
    op.drop_index("ix_audit_log_correlation_id", table_name="audit_log")
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_actor_user_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_password_reset_tokens_consumed_at", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_expires_at", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_index("ix_auth_sessions_revoked_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_expires_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_token_hash", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")

    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_table("user_roles")

    op.drop_index("ix_users_employee_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")
