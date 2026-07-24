"""Database session helper for HPD CLI Core.

Usage:
    from hpd_cli.db import get_session
    with get_session() as session:
        projects = session.query(Project).all()
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from hpd_cli.models import Base

HPD_HOME = Path(os.environ.get("HPD_HOME", Path.home() / ".hpd"))
DEFAULT_DB_URL = f"sqlite:///{HPD_HOME / 'hpd.db'}"


def get_engine(db_url: str | None = None):
    """Create or return a SQLAlchemy engine.

    Uses HPD_DATABASE_URL env var, or falls back to ~/.hpd/hpd.db.
    """
    url = db_url or os.environ.get("HPD_DATABASE_URL", DEFAULT_DB_URL)
    return create_engine(url, echo=False)


def get_session(db_url: str | None = None):
    """Get a new SQLAlchemy session for the HPD database."""
    engine = get_engine(db_url)
    return Session(engine)


def init_db(db_url: str | None = None):
    """Create all tables (for first-time setup)."""
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    return engine
