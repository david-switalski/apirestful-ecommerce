#!/bin/sh
set -e
 
cd /app

echo "INFO: Running database migrations..."
python -m alembic upgrade head

echo "INFO: Starting application..."
exec "$@"