#!/bin/sh
set -e

echo "INFO: Running database migrations..."
python -m alembic -c /app/alembic.ini upgrade head

echo "INFO: Starting application..."
exec "$@"