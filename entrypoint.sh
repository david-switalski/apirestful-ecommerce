#!/bin/sh
set -e
 
cd /app

echo "INFO: Running database migrations..."
alembic upgrade head

echo "INFO: Creating superuser if it does not exist..."
python -m scripts.create_super_user

echo "INFO: Starting application..."
exec "$@"