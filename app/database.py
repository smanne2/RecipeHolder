"""
Database management and session handling.
Provides database engine, session factory, and utility functions.
"""
import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models import Base

logger = logging.getLogger(__name__)


# Enable foreign keys for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints in SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Create database engine
engine = create_engine(
    f"sqlite:///{settings.database_path}",
    echo=settings.log_level == "DEBUG",
    connect_args={"check_same_thread": False},  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    Initialize database by creating all tables.
    Called on application startup.
    """
    logger.info(f"Initializing database at {settings.database_path}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Yields a session and ensures it's closed after use.
    
    Usage in FastAPI:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session for non-FastAPI contexts.
    Caller is responsible for closing the session.
    
    Returns:
        SQLAlchemy Session instance
    """
    return SessionLocal()
