#!/bin/bash

# Apply database migrations
echo "Applying database migrations..."
python arkad/manage.py migrate

# Start server
echo "Starting server..."
python arkad/manage.py runserver 0.0.0.0:8000
