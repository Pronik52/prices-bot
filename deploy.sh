#!/usr/bin/env bash
#
# Быстрое обновление проекта на сервере: подтянуть код и пересобрать стек.
# Использует Docker Compose v2 (docker compose). Запуск: ./deploy.sh
#
set -euo pipefail

# Работаем из каталога скрипта, откуда бы его ни запустили
cd "$(dirname "$0")"

echo "==> [1/4] Обновляю код (git pull)"
if [ -d .git ]; then
    git pull --ff-only
else
    echo "    не git-репозиторий — пропускаю"
fi

echo "==> [2/4] Останавливаю текущие контейнеры (данные в томах сохраняются)"
docker compose down

echo "==> [3/4] Собираю образы и поднимаю стек"
docker compose up -d --build

echo "==> [4/4] Статус сервисов"
docker compose ps

echo
echo "Готово. Полезные команды:"
echo "  docker compose logs -f bot            # логи бота"
echo "  docker compose logs --tail=30 api     # логи API"
echo "  docker compose logs -f celery_worker  # логи парсинга"
