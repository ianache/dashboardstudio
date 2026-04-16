from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=settings.debug
)

@event.listens_for(engine, "connect")
def set_search_path(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute(f'SET search_path TO "{settings.postgres_schema}", public')
    cursor.close()

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