"""Database Migration Utility: SQLite to MySQL

Safely migrates existing canonical employee records from local SQLite (ems_local.db)
to the target MySQL database without overwriting or deleting any existing SQLite data.
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.models import EmployeeModel
from app.config import settings, backend_dir


def get_sqlite_source_session():
    """Explicitly connects to the local SQLite database file (ems_local.db)

    regardless of what DATABASE_URL is configured in .env.
    """
    sqlite_db_path = backend_dir / "ems_local.db"
    if not sqlite_db_path.exists():
        raise FileNotFoundError(f"SQLite database file not found at: {sqlite_db_path}")

    # Use 3 slashes for absolute path on Windows
    normalized_path = str(sqlite_db_path).replace("\\", "/")
    sqlite_url = f"sqlite:///{normalized_path}"
    sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, echo=False)
    return sessionmaker(bind=sqlite_engine)()


def test_mysql_connection(mysql_url: str):
    """Verifies that the target MySQL database is reachable and credentials are valid."""
    safe_display = mysql_url.split("@")[-1] if "@" in mysql_url else mysql_url
    print(f"Testing connectivity to target MySQL database: {safe_display}...")
    try:
        target_engine = create_engine(mysql_url, echo=False)
        with target_engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION();")).scalar()
            print(f"✓ Connected successfully! MySQL Server version: {result}")
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)


def run_migration(mysql_url: str = None) -> bool:
    """Migrates canonical employee records from SQLite to MySQL."""
    if not mysql_url:
        mysql_url = settings.DATABASE_URL

    if not mysql_url.startswith("mysql"):
        print("❌ Error: Target DATABASE_URL does not specify a MySQL connection.")
        print(f"Current URL begins with: {mysql_url.split('://')[0]}://")
        return False

    # 1. Test Connection
    is_connected, msg = test_mysql_connection(mysql_url)
    if not is_connected:
        print(f"❌ Migration Aborted: Cannot connect to MySQL.\nError: {msg}")
        return False

    try:
        target_engine = create_engine(mysql_url, echo=False)
        TargetSession = sessionmaker(bind=target_engine)

        # Schema must be provisioned by the reviewed Alembic migration plan.
        if not inspect(target_engine).has_table("employees"):
            print(
                "Migration aborted: employees table is absent. "
                "Provision schema through the approved Alembic process first."
            )
            return False

        # 3. Read canonical records from SQLite
        sqlite_db = get_sqlite_source_session()
        canonical_employees = sqlite_db.query(EmployeeModel).all()
        print(f"Found {len(canonical_employees)} employee records in SQLite source database.")

        # 4. Migrate records into MySQL (safe against duplicates)
        mysql_db = TargetSession()
        migrated_count = 0
        skipped_count = 0

        for emp in canonical_employees:
            existing = mysql_db.query(EmployeeModel).filter(
                (EmployeeModel.employee_code == emp.employee_code) |
                (EmployeeModel.email == emp.email)
            ).first()

            if existing:
                skipped_count += 1
                print(f" - Skipped (already exists): {emp.employee_code} ({emp.email})")
            else:
                new_emp = EmployeeModel(
                    id=emp.id,
                    employee_code=emp.employee_code,
                    first_name=emp.first_name,
                    last_name=emp.last_name,
                    email=emp.email,
                    phone_number=emp.phone_number or "",
                    job_title=emp.job_title,
                    department=emp.department,
                    date_of_joining=emp.date_of_joining,
                    employment_status=emp.employment_status,
                    created_at=emp.created_at,
                    updated_at=emp.updated_at,
                )
                mysql_db.add(new_emp)
                migrated_count += 1
                print(f" + Migrated to MySQL: {emp.employee_code}: {emp.first_name} {emp.last_name}")

        mysql_db.commit()

        # 5. Verification
        total_in_mysql = mysql_db.query(EmployeeModel).count()
        print(f"\nMigration Summary:")
        print(f" - Records newly migrated: {migrated_count}")
        print(f" - Records skipped (already existing): {skipped_count}")
        print(f" - Total records in MySQL database: {total_in_mysql}")

        sqlite_db.close()
        mysql_db.close()
        return True

    except Exception as e:
        print(f"❌ Error during data migration: {e}")
        return False


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_migration(url_arg)
    sys.exit(0 if success else 1)
