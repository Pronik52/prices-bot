"""Engine и фабрика сессий. Общие для API (FastAPI) и воркеров (Celery).

Используется синхронный SQLAlchemy: это единственный слой доступа к данным,
и он должен одинаково работать в FastAPI (эндпоинты выполняются в threadpool)
и в Celery-задачах (которые синхронны по своей природе).
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://app:change_me@localhost:5432/price_tracker",
)

# Параметры пула не применимы к SQLite (используется в тестах/локально)
_engine_kwargs: dict = {"future": True, "pool_pre_ping": True}
if not DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Транзакционный контекст-менеджер для воркеров и скриптов."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
