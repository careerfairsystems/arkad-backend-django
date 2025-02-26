#!/bin/bash

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files"
python manage.py collectstatic --noinput

#gunicorn --workers 8 --timeout 16 --bind 0.0.0.0:8000 arkad.wsgi:application