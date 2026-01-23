#!/bin/bash
#If any step fails. It will stop
echo "STARTING..."
echo "SET -E option"
set -e
pwd


echo "RUNNING MAKE MIGRATIONS: manage.py makemigrations"
python manage.py makemigrations --no-input

echo "RUNNING DJANGO MIGRATIONS: manage.py migrate"
python manage.py migrate

echo "RUNNING COLLECT STATIC: collectstatic"
python manage.py collectstatic --no-input --clear

echo "RUNNING manage.py create_admin_user"
python manage.py create_admin_user

echo "--- STARTING SERVER ---"
exec "$@"
