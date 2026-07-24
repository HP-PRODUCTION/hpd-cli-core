"""Database session helper for HPD CLI Core.

Usage:
    from hpd_cli.db import get_session
    with get_session() as session:
        projects = session.query(Project).all()

Supports SQLite (default) and PostgreSQL via HPD_DATABASE_URL.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from hpd_cli.models import Base

HPD_HOME = Path(os.environ.get("HPD_HOME", Path.home() / ".hpd"))
DEFAULT_DB_URL = f"sqlite:///{HPD_HOME / 'hpd.db'}"


def is_postgres_url(url: str) -> bool:
    """Check if the URL points to a PostgreSQL database."""
    return url.startswith("postgresql://") or url.startswith("postgresql+psycopg2://")


def get_engine(db_url: str | None = None):
    """Create or return a SQLAlchemy engine.

    Uses HPD_DATABASE_URL env var, or falls back to ~/.hpd/hpd.db.
    Auto-detects SQLite vs PostgreSQL.
    """
    url = db_url or os.environ.get("HPD_DATABASE_URL", DEFAULT_DB_URL)
    kwargs = {"echo": False}

    if is_postgres_url(url):
        # PostgreSQL: pool settings for production
        kwargs["pool_size"] = int(os.environ.get("HPD_DB_POOL_SIZE", "5"))
        kwargs["max_overflow"] = int(os.environ.get("HPD_DB_MAX_OVERFLOW", "10"))
        kwargs["pool_pre_ping"] = True
    else:
        # SQLite: single-threaded, WAL mode
        kwargs["connect_args"] = {"check_same_thread": False}

    return create_engine(url, **kwargs)


def get_session(db_url: str | None = None):
    """Get a new SQLAlchemy session for the HPD database."""
    engine = get_engine(db_url)
    return Session(engine)


def init_db(db_url: str | None = None):
    """Create all tables (for first-time setup).

    Works with both SQLite and PostgreSQL.
    """
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    return engine

