"""
Fahamu Shamba - Database Configuration
SQLite by default; set DATABASE_URL env var for PostgreSQL in production.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///fahamu_shamba.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=os.getenv("DEBUG", "false").lower() == "true",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables via SQLAlchemy models if available."""
    try:
        from models import Base as ModelBase
        ModelBase.metadata.create_all(bind=engine)
        print("Database tables created.")
    except ImportError:
        print("No models.py found; skipping SQLAlchemy table creation.")


if __name__ == "__main__":
    init_db()
