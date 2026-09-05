import os
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL
from backend.database.models import Base


def get_engine(database_url=None):
    url = database_url or DATABASE_URL
    engine = create_engine(url, future=True)
    return engine


def init_db(database_url=None):
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine


def get_session_factory(database_url=None):
    engine = get_engine(database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def utc_now():
    return datetime.now(timezone.utc)
