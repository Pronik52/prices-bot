"""Роуты CRUD отслеживаемых товаров и истории цен."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, verify_internal_token
from api.queue import enqueue_parse_item
from api.schemas.item import (
    ItemCreate,
    ItemPriceHistoryRead,
    ItemRead,
    PricePointRead,
)
from api.services.tracking_service import (
    DuplicateItemError,
    InvalidItemUrlError,
    LimitReachedError,
    TrackingService,
)
from db.repositories.item_repository import ItemRepository

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(verify_internal_token)],
)


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def add_item(payload: ItemCreate, session: Session = Depends(get_db)) -> ItemRead:
    service = TrackingService(session)
    try:
        item = service.add_item(
            telegram_id=payload.telegram_id,
            url=payload.url,
            target_price=payload.target_price,
        )
    except InvalidItemUrlError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except DuplicateItemError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except LimitReachedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc

    # Немедленный парсинг: цена появится в «Мои товары» через пару секунд
    enqueue_parse_item(item.id)
    return item


@router.get("", response_model=list[ItemRead])
def list_items(
    telegram_id: int = Query(...), session: Session = Depends(get_db)
) -> list[ItemRead]:
    service = TrackingService(session)
    return service.list_items(telegram_id)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int, telegram_id: int = Query(...), session: Session = Depends(get_db)
) -> Response:
    service = TrackingService(session)
    if not service.remove_item(telegram_id, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{item_id}/history", response_model=ItemPriceHistoryRead)
def price_history(
    item_id: int,
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_db),
) -> ItemPriceHistoryRead:
    repo = ItemRepository(session)
    if repo.get_by_id(item_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    points = repo.get_price_history(item_id, limit=limit)
    return ItemPriceHistoryRead(
        item_id=item_id,
        history=[PricePointRead.model_validate(p) for p in points],
    )
