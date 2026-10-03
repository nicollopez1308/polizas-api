"""Conexión a la base de datos."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db() -> Iterator[Session]:
    """Abre una sesión para una petición y la cierra al terminar, pase lo que pase."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()