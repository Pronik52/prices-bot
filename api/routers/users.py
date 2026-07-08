"""Роуты управления пользователями."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, verify_internal_token
from api.schemas.user import UserCreate, UserRead
from db.repositories.user_repository import UserRepository

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(verify_internal_token)],
)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_or_get_user(payload: UserCreate, session: Session = Depends(get_db)) -> UserRead:
    """Регистрирует пользователя по telegram_id (идемпотентно)."""
    repo = UserRepository(session)
    user = repo.get_or_create(payload.telegram_id, payload.username)
    session.commit()
    return user


@router.get("/{telegram_id}", response_model=UserRead)
def get_user(telegram_id: int, session: Session = Depends(get_db)) -> UserRead:
    repo = UserRepository(session)
    user = repo.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return user
