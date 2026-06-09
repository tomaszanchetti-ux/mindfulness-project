"""Motor de DB + sesión. Espejo de Arc One (SQLAlchemy 2 + psycopg3 + pool)."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..config import settings


class Base(DeclarativeBase):
    """Base declarativa común a todas las tablas."""


# pool_pre_ping = sobrevive a conexiones que Cloud SQL cierra por inactividad.
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Dependency de FastAPI: una sesión por request, siempre cerrada."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
