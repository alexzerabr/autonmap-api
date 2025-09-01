#!/usr/bin/env sh
# migrate.sh

set -e

TARGET="${1:-backend}"

if command -v wait-for.sh >/dev/null 2>&1; then
    wait-for.sh "${DB_HOST:-db}:5432"
fi

case "$TARGET" in
  backend)
    echo "Running Alembic migrations for the backend..."
    alembic upgrade head
    ;;
  frontend)
    echo "Running Flask migrations for the frontend..."
    flask db upgrade
    ;;
  *)
    echo "Unknown migration target: $TARGET" >&2
    exit 1
    ;;
esac
