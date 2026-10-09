"""Alembic env. WHY: autogenerate from Base.metadata = single source of truth."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db.base import Base
import app.models  # noqa: F401  -- WHY: registers all tables

config = context.config
# WHY: allow DATABASE_URL env override for local Postgres.
if os.getenv("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
