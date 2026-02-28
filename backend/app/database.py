"""
Database configuration and session management.

Uses SQLAlchemy with SQLite for local persistent storage.
The database file is created in the backend/data/ directory.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ── Database path ──────────────────────────────────────────────────────────
# Store the SQLite database in the data/ directory relative to backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'tasks.db')}"

# ── Engine & Session ──────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Base class for all ORM models ─────────────────────────────────────────
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session.
    Ensures the session is closed after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined by ORM models."""
    Base.metadata.create_all(bind=engine)
