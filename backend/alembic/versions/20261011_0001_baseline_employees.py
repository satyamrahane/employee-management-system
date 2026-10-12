"""Baseline employees schema for fresh databases only.

Revision ID: 20261011_0001
Revises: None
Create Date: 2026-10-11

This revision is derived from backend/app/models.py.  It must NOT be upgraded
against an existing EMS database until that database has been backed up and its
live schema has been compared with this baseline.  For a matching existing
database, the approved operation is `alembic stamp 20261011_0001`, not
`alembic upgrade head`.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20261011_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the ORM-defined employees table in a fresh, empty database."""
    op.create_table(
        "employees",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("employee_code", sa.String(length=20), nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("job_title", sa.String(length=100), nullable=False),
        sa.Column("department", sa.String(length=50), nullable=False),
        sa.Column("date_of_joining", sa.String(length=10), nullable=False),
        sa.Column("employment_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    # Names follow SQLAlchemy's default generated-index convention used by the
    # current model.  The primary-key index is redundant but retained because
    # EmployeeModel declares index=True on id.
    op.create_index("ix_employees_id", "employees", ["id"], unique=False)
    op.create_index("ix_employees_employee_code", "employees", ["employee_code"], unique=True)
    op.create_index("ix_employees_email", "employees", ["email"], unique=True)
    op.create_index("ix_employees_department", "employees", ["department"], unique=False)
    op.create_index("ix_employees_employment_status", "employees", ["employment_status"], unique=False)


def downgrade() -> None:
    """Remove the fresh-database baseline table when explicitly rolled back."""
    op.drop_index("ix_employees_employment_status", table_name="employees")
    op.drop_index("ix_employees_department", table_name="employees")
    op.drop_index("ix_employees_email", table_name="employees")
    op.drop_index("ix_employees_employee_code", table_name="employees")
    op.drop_index("ix_employees_id", table_name="employees")
    op.drop_table("employees")
