"""DI-зависимости FastAPI: сессия БД, аутентификация, текущий пользователь."""
from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from api.config import Settings, get_settings
from db.repositories.user_repository import UserRepository
from db.session import SessionLocal


def get_db() -> Iterator[Session]:
    """Сессия БД на время запроса. Commit — явный в роутере/сервисе."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def verify_internal_token(
    x_internal_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Простая аутентификация вызовов от доверенных клиентов (бот, воркер).

    На Стадии 1 достаточно общего секрета в заголовке X-Internal-Token.
    """
    if x_internal_token != settings.internal_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )


def get_user_repo(session: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(session)
