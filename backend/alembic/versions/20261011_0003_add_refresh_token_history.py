"""Add consumed refresh-token history.

Revision ID: 20261011_0003
Revises: 20261011_0002
Create Date: 2026-10-11

This forward revision changes only authentication tables.  It stores consumed
token hashes, never raw refresh tokens, and does not alter the employees table.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261011_0003"
down_revision: Union[str, Sequence[str], None] = "20261011_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MYSQL_TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.add_column(
        "auth_sessions",
        sa.Column(
            "current_refresh_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE auth_sessions "
            "SET current_refresh_expires_at = expires_at "
            "WHERE current_refresh_expires_at IS NULL"
        )
    )
    op.alter_column(
        "auth_sessions",
        "current_refresh_expires_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
        nullable=False,
    )

    op.create_table(
        "auth_refresh_token_history",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["auth_sessions.id"],
            name="fk_auth_refresh_token_history_session_id_auth_sessions",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("token_hash"),
        **MYSQL_TABLE_OPTIONS,
    )
    op.create_index(
        "ix_auth_refresh_token_history_session_id_expires_at",
        "auth_refresh_token_history",
        ["session_id", "expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_auth_refresh_token_history_expires_at",
        "auth_refresh_token_history",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("auth_refresh_token_history")
    op.drop_column("auth_sessions", "current_refresh_expires_at")
