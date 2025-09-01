set -e

echo "INFO: Running database migrations..."
python -m alembic upgrade head

echo "INFO: Starting application..."
exec "$@"