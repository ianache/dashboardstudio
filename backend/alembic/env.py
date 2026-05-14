from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text, event
from alembic import context
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import get_settings
from app.core.database import Base
from app.models import models

config = context.config
settings = get_settings()

if settings.database_url:
    config.set_main_option('sqlalchemy.url', settings.database_url.replace('postgresql://', 'postgresql+psycopg2://'))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=settings.postgres_schema,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Set search_path at the psycopg2 level (before autobegin) so it doesn't
    # interfere with SQLAlchemy 2.0 autobegin / context.begin_transaction().
    @event.listens_for(connectable, "connect")
    def set_search_path(dbapi_conn, _rec):
        existing = dbapi_conn.autocommit
        dbapi_conn.autocommit = True
        cur = dbapi_conn.cursor()
        cur.execute(f"SET SESSION search_path TO {settings.postgres_schema}")
        cur.close()
        dbapi_conn.autocommit = existing

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=settings.postgres_schema,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()