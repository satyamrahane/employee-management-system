"""Startup and development-seed safety tests; no production lifespan or DB."""

import ast
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.dev_seed import SeedRefusedError, main, seed_demo_employees
from app.models import EmployeeModel


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _called_names(tree):
    return {
        node.func.id
        if isinstance(node.func, ast.Name)
        else node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            or isinstance(node.func, ast.Attribute)
        )
    }


def test_main_has_no_automatic_schema_or_seed_startup():
    main_source = (BACKEND_DIR / "app" / "main.py").read_text(encoding="utf-8")
    database_source = (BACKEND_DIR / "app" / "database.py").read_text(
        encoding="utf-8"
    )
    main_tree = ast.parse(main_source)
    database_tree = ast.parse(database_source)

    assert not _called_names(main_tree).intersection(
        {"create_all", "init_db", "seed_sample_data"}
    )
    assert not _called_names(database_tree).intersection({"create_all"})
    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "lifespan"
        for node in main_tree.body
    )
    assert "auth_api" not in main_source


def _unused_engine_factory(_url):
    pytest.fail("Rejected seed target must not create an engine.")


@pytest.mark.parametrize(
    ("app_env", "database_url", "message"),
    [
        (
            "production",
            "sqlite:///unused.sqlite",
            "development",
        ),
        (
            "development",
            "mysql+pymysql://user:password@localhost/ems",
            "SQLite",
        ),
        (
            "development",
            "postgresql://localhost/ems",
            "SQLite",
        ),
    ],
)
def test_seeder_refuses_unsafe_mode_or_backend(
    app_env,
    database_url,
    message,
):
    with pytest.raises(SeedRefusedError, match=message):
        seed_demo_employees(
            app_env=app_env,
            database_url=database_url,
            engine_factory=_unused_engine_factory,
        )


def test_cli_prints_clear_production_refusal(monkeypatch, capsys):
    monkeypatch.setattr(settings, "APP_ENV", "production")

    exit_code = main()

    assert exit_code == 2
    output = capsys.readouterr().out
    assert "APP_ENV" in output
    assert "development" in output


def test_seeder_refuses_missing_file_without_creating_it(tmp_path):
    missing_database = tmp_path / "missing.sqlite"

    with pytest.raises(SeedRefusedError, match="file is absent"):
        seed_demo_employees(
            app_env="development",
            database_url=f"sqlite:///{missing_database.as_posix()}",
        )

    assert not missing_database.exists()


def test_seeder_refuses_database_without_alembic_created_table(tmp_path):
    database_path = tmp_path / "no_schema.sqlite"
    database_path.touch()

    with pytest.raises(SeedRefusedError, match="table is absent"):
        seed_demo_employees(
            app_env="development",
            database_url=f"sqlite:///{database_path.as_posix()}",
        )


def test_seeder_only_seeds_empty_sqlite_and_refuses_second_run(tmp_path):
    database_path = tmp_path / "development.sqlite"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = create_engine(database_url)
    EmployeeModel.__table__.create(engine)
    engine.dispose()

    inserted = seed_demo_employees(
        app_env="development",
        database_url=database_url,
    )
    assert inserted == 6

    with pytest.raises(SeedRefusedError, match="Employees already exist"):
        seed_demo_employees(
            app_env="development",
            database_url=database_url,
        )

    verification_engine = create_engine(database_url)
    with Session(verification_engine) as session:
        count = session.scalar(select(func.count()).select_from(EmployeeModel))
        employee_codes = set(
            session.scalars(select(EmployeeModel.employee_code)).all()
        )
    verification_engine.dispose()

    assert count == 6
    assert employee_codes == {f"EMP-{number}" for number in range(1001, 1007)}
