#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Run database migrations
echo "Running migrations..."
python manage.py migrate

# Pulling static vendor files
echo "Pulling static files"
python manage.py vendor_pull

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Check if a superuser exists, and create one if it doesn't
echo "Ensuring superuser exists..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin');
"

# Run the Django development server
exec "$@"
