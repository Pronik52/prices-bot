# Price Tracker (Стадия 1 — MVP)

Трекер цен на маркетплейсах (Wildberries, Ozon) с уведомлениями в Telegram.

## Архитектура

Система разделена на слои с чёткими границами — каждый масштабируется отдельно:

| Слой | Каталог | Роль |
|------|---------|------|
| Telegram-бот | `bot/` | Только UI: приём команд, вызов API через HTTP. Без бизнес-логики. |
| API (FastAPI) | `api/` | Мозг: пользователи, товары, подписки, лимиты по тарифу. |
| Планировщик + очередь | `worker/` | Celery Beat раскидывает per-item задачи в Redis-очередь. |
| Парсеры | `parsers/` | Изолированный слой: `BaseParser` + наследники по маркетплейсам. |
| Слой данных | `db/` | Общий для API и воркеров: модели, репозитории (sync SQLAlchemy). |
| Общее | `shared/` | Enum'ы (`Marketplace`, `SubscriptionTier`), логирование. |

Поток данных: `bot → api → db`, а параллельно `beat → check_prices → parse_item → (parser) → db → send_notification → Telegram`.

## Запуск

```bash
cp .env.example .env          # заполнить BOT_TOKEN и DB_PASSWORD
docker compose up --build
```

Поднимутся 5 сервисов + одноразовый прогон миграций (`migrate`).
API-доки: http://localhost:8000/docs

## Разработка / тесты

```bash
python -m venv .venv && source .venv/bin/activate   # Python 3.12
pip install -r requirements.txt
pytest                                               # тесты без сети (sqlite)
```

> Тесты работают на SQLite in-memory; прод — PostgreSQL.
> ORM использует `Mapped[str | None]` (PEP 604), поэтому требуется **Python 3.10+**.

## Миграции

```bash
alembic revision --autogenerate -m "описание"   # создать миграцию
alembic upgrade head                            # применить
```
`DATABASE_URL` берётся из окружения (`migrations/env.py`).

## Что реализовано на Стадии 1

- ✅ Регистрация пользователя, тарифы (`free`/`premium`) с лимитами товаров.
- ✅ Добавление/список/удаление товаров через бота → API, валидация ссылок.
- ✅ WB-парсер через публичный `card.wb.ru` (с retry и ротацией прокси).
- ✅ Периодический обход цен (Celery Beat) и уведомления при достижении цели.
- ✅ История цен, журнал уведомлений (анти-спам).

## Заглушки / Стадия 2

- Ozon-парсер (`parsers/ozon.py`) — извлекает артикул, но парсинг цены требует
  antibot-обхода.
- Платежи (`api/routers/subscriptions.py`) — смена тарифа без реальной оплаты;
  вебхуки ЮKassa/Stripe — позже.
