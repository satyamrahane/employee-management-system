"""Offline Alembic revision tests; no env.py or configured database access."""

from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import re
import sqlite3

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy.dialects import mysql


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = BACKEND_DIR / "alembic" / "versions"
REVISION_FILES = {
    "20261011_0001": "20261011_0001_baseline_employees.py",
    "20261011_0002": "20261011_0002_add_authentication_schema.py",
    "20261011_0003": "20261011_0003_add_refresh_token_history.py",
}


def _load_revision(revision_id: str):
    module_path = MIGRATIONS_DIR / REVISION_FILES[revision_id]
    spec = spec_from_file_location(f"offline_{revision_id}", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _render_upgrade(module) -> str:
    output = StringIO()
    context = MigrationContext.configure(
        dialect=mysql.dialect(),
        opts={
            "as_sql": True,
            "output_buffer": output,
            "literal_binds": True,
        },
    )
    with Operations.context(context):
        module.upgrade()
    return output.getvalue()


def test_revision_graph_has_expected_single_head():
    config = Config()
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["20261011_0003"]
    assert script.get_revision("20261011_0001").down_revision is None
    assert (
        script.get_revision("20261011_0002").down_revision
        == "20261011_0001"
    )
    assert (
        script.get_revision("20261011_0003").down_revision
        == "20261011_0002"
    )


def test_0001_mysql_offline_sql_describes_employee_baseline():
    sql = _render_upgrade(_load_revision("20261011_0001"))

    assert "CREATE TABLE employees" in sql
    assert "ix_employees_employee_code" in sql
    assert "ix_employees_email" in sql
    assert "ix_employees_department" in sql
    assert "ix_employees_employment_status" in sql
    assert "users" not in sql


def test_0002_role_seed_includes_shared_utc_created_at(monkeypatch):
    module = _load_revision("20261011_0002")
    fixed_timestamp = datetime(2031, 4, 5, 6, 7, 8, tzinfo=timezone.utc)

    class FixedDateTime:
        @classmethod
        def now(cls, tz=None):
            assert tz is timezone.utc
            return fixed_timestamp

    monkeypatch.setattr(module, "datetime", FixedDateTime)
    sql = _render_upgrade(module)

    assert "CREATE TABLE roles" in sql
    assert "created_at DATETIME NOT NULL" in sql
    assert "ix_roles_name" in sql
    inserts = re.findall(
        r"INSERT INTO roles \(id, name, created_at\) VALUES .*?;",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert len(inserts) == 2
    assert "role-admin" in inserts[0] and "ADMIN" in inserts[0]
    assert "role-hr" in inserts[1] and "HR" in inserts[1]
    assert all("2031-04-05 06:07:08'" in statement for statement in inserts)
    assert all("+00:00" not in statement for statement in inserts)
    assert "CREATE TABLE users" in sql
    assert "fk_users_employee_id_employees" in sql
    assert "ON DELETE SET NULL" in sql
    assert "CREATE TABLE user_roles" in sql
    assert "ON DELETE RESTRICT" in sql
    assert "ON DELETE CASCADE" in sql
    assert "CREATE TABLE auth_sessions" in sql
    assert "CREATE TABLE password_reset_tokens" in sql
    assert "CREATE TABLE audit_log" in sql


def test_0003_offline_backfill_preserves_absolute_expiry_and_existing_value():
    sql = _render_upgrade(_load_revision("20261011_0003"))
    match = re.search(
        r"UPDATE auth_sessions\s+"
        r"SET current_refresh_expires_at = expires_at\s+"
        r"WHERE current_refresh_expires_at IS NULL\s*;",
        sql,
        flags=re.IGNORECASE,
    )
    assert match is not None
    backfill_sql = match.group(0)
    assert "SET expires_at" not in backfill_sql

    with sqlite3.connect(":memory:") as connection:
        connection.execute(
            "CREATE TABLE auth_sessions ("
            "id TEXT PRIMARY KEY, expires_at TEXT NOT NULL, "
            "current_refresh_expires_at TEXT NULL)"
        )

        connection.execute(backfill_sql)
        assert connection.execute(
            "SELECT COUNT(*) FROM auth_sessions"
        ).fetchone()[0] == 0

        connection.executemany(
            "INSERT INTO auth_sessions VALUES (?, ?, ?)",
            [
                ("ses-null", "2032-01-01 00:00:00", None),
                ("ses-valid", "2033-01-01 00:00:00", "2032-12-01 00:00:00"),
            ],
        )
        connection.execute(backfill_sql)
        rows = dict(
            connection.execute(
                "SELECT id, current_refresh_expires_at FROM auth_sessions"
            ).fetchall()
        )

    assert rows == {
        "ses-null": "2032-01-01 00:00:00",
        "ses-valid": "2032-12-01 00:00:00",
    }
