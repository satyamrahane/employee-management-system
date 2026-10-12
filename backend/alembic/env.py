"""Alembic environment for the EMS backend.

The database URL is read at invocation time from the existing application
settings.  It is intentionally not stored in alembic.ini or migration files.
Running an Alembic command may connect to the configured database; this module
performs no connection merely by being present in the repository.
"""

from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool


# Allow `alembic -c alembic.ini ...` when invoked from backend/.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.database import Base
import app.models  # noqa: F401 - imports ORM mappings into Base.metadata
import app.auth_models  # noqa: F401 - auth mappings are migration-controlled


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Never place a credential-bearing URL in alembic.ini.  This is intentionally
# assigned only in process memory from the existing configuration source.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without creating a database connection."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the configured database when explicitly invoked."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
