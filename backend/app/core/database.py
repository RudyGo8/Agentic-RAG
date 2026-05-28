'''
@create_time: 2025/10/21
@Author: GeChao
@File: database.py
'''
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE
from app.utils.log import get_logger

import pymysql

logger = get_logger(__name__)
pymysql.install_as_MySQLdb()

SQLALCHEMY_DATABASE_URL = f"mysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_size=10,
    pool_recycle=3600,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    try:
        # Import all models before metadata initialization so SQLAlchemy can
        # resolve relationship() string targets consistently.
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        logger.info("database_initialized")
    except Exception:
        logger.exception("database_init_failed")
        raise
