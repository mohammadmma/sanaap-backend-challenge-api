#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser..."
python manage.py create_default_superuser

echo "Starting server..."
exec gunicorn project.wsgi:application --bind 0.0.0.0:8000