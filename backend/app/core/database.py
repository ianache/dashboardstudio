from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import get_settings

settings = get_settings()

# Use connect_args to set search_path on every connection (PostgreSQL specific)
connect_args = {
    "options": f"-c search_path={settings.postgres_schema},public"
}

engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=settings.debug,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_schema():
    return settings.postgres_schema


def init_db():
    from app.models import models
    Base.metadata.create_all(bind=engine)
