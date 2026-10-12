"""Explicit development-only employee demo-data seeder.

Run from ``backend/`` with ``APP_ENV=development`` and an existing SQLite
schema created through Alembic. This command never creates tables or replaces
existing employees.
"""

from pathlib import Path
from typing import Callable

from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.engine import Engine, URL, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .models import EmployeeModel


class SeedRefusedError(RuntimeError):
    """Raised when demo seeding is not explicitly safe for this target."""


_DEMO_EMPLOYEES = (
    {
        "employee_code": "EMP-1001",
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya.sharma@example.com",
        "phone_number": "+1 (555) 234-5678",
        "job_title": "Senior Software Engineer",
        "department": "Engineering",
        "date_of_joining": "2023-03-15",
        "employment_status": "ACTIVE",
    },
    {
        "employee_code": "EMP-1002",
        "first_name": "Marcus",
        "last_name": "Vance",
        "email": "marcus.vance@example.com",
        "phone_number": "+1 (555) 345-6789",
        "job_title": "Lead Product Designer",
        "department": "Design",
        "date_of_joining": "2022-08-01",
        "employment_status": "ACTIVE",
    },
    {
        "employee_code": "EMP-1003",
        "first_name": "Amina",
        "last_name": "El-Sayed",
        "email": "amina.elsayed@example.com",
        "phone_number": "+1 (555) 456-7890",
        "job_title": "Product Manager",
        "department": "Product",
        "date_of_joining": "2023-01-10",
        "employment_status": "ACTIVE",
    },
    {
        "employee_code": "EMP-1004",
        "first_name": "Daniel",
        "last_name": "Kowalski",
        "email": "daniel.kowalski@example.com",
        "phone_number": "+1 (555) 567-8901",
        "job_title": "HR Operations Specialist",
        "department": "Human Resources",
        "date_of_joining": "2021-11-15",
        "employment_status": "ACTIVE",
    },
    {
        "employee_code": "EMP-1005",
        "first_name": "Sophia",
        "last_name": "Chen",
        "email": "sophia.chen@example.com",
        "phone_number": "+1 (555) 678-9012",
        "job_title": "Financial Analyst",
        "department": "Finance",
        "date_of_joining": "2023-06-01",
        "employment_status": "ACTIVE",
    },
    {
        "employee_code": "EMP-1006",
        "first_name": "Liam",
        "last_name": "O'Connor",
        "email": "liam.oconnor@example.com",
        "phone_number": "+1 (555) 789-0123",
        "job_title": "Growth Marketing Manager",
        "department": "Marketing",
        "date_of_joining": "2022-04-18",
        "employment_status": "INACTIVE",
    },
)


def _validate_target(app_env: str, database_url: str) -> URL:
    if app_env != "development":
        raise SeedRefusedError(
            "Seeding requires APP_ENV to be explicitly set to development."
        )

    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        raise SeedRefusedError(
            "Seeding is allowed only for a pre-existing SQLite database."
        )

    database_path = url.database
    if (
        not database_path
        or database_path == ":memory:"
        or database_path.startswith("file:")
    ):
        raise SeedRefusedError(
            "Seeding requires an existing SQLite file and Alembic schema."
        )
    if not Path(database_path).is_file():
        raise SeedRefusedError(
            "SQLite file is absent; create the schema with Alembic first."
        )
    return url


def seed_demo_employees(
    *,
    app_env: str | None = None,
    database_url: str | None = None,
    engine_factory: Callable[[URL], Engine] = create_engine,
) -> int:
    """Insert demo employees into an existing, empty SQLite table."""
    environment = settings.APP_ENV if app_env is None else app_env
    configured_url = (
        settings.DATABASE_URL if database_url is None else database_url
    )
    url = _validate_target(environment, configured_url)
    engine = engine_factory(url)
    try:
        if not inspect(engine).has_table("employees"):
            raise SeedRefusedError(
                "Employees table is absent; create it with Alembic first."
            )

        with Session(engine) as session:
            with session.begin():
                employee_count = session.scalar(
                    select(func.count()).select_from(EmployeeModel)
                )
                if employee_count:
                    raise SeedRefusedError(
                        "Employees already exist; no records were changed."
                    )
                session.add_all(
                    EmployeeModel(**employee_data)
                    for employee_data in _DEMO_EMPLOYEES
                )
        return len(_DEMO_EMPLOYEES)
    finally:
        engine.dispose()


def main() -> int:
    try:
        inserted = seed_demo_employees()
    except SeedRefusedError as error:
        print(f"Development seed refused: {error}")
        return 2
    except SQLAlchemyError:
        print("Development seed failed; the transaction was rolled back.")
        return 1

    print(f"Inserted {inserted} development demo employees.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
