#!/bin/bash
set -e

# Wait for Postgres to start up
until pg_isready -h $DB_HOST_CMS -p $DB_PORT_CMS -U $DB_USER_CMS
do
  echo "PORT $DB_HOST_CMS"

  echo "Waiting for database to start up..."
  sleep 1
done

# Apply database migrations
python manage.py makemigrations
python manage.py migrate --noinput

python manage.py collectstatic --no-input
# python manage.py loaddata dumpdata.json

exec "$@"