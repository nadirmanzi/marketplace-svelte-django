#!/bin/sh

# Wait for postgres
echo "Waiting for postgres..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser
echo "Ensuring superuser exists..."
python manage.py ensure_admin

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Execute command passed to docker run
exec "$@"
