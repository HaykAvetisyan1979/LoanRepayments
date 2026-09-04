#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status



# Wait for the database to be ready
echo "Waiting for postgres..."
while ! python -c "import socket; s = socket.socket(); s.connect(('$DB_HOST', int('$DB_PORT')))" > /dev/null 2>&1; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Postgres is up - executing commands"




python manage.py makemigrations
# python manage.py makemigrations --merge --no-input # ← merge if needed  Լոկալ և սերվերի վրա աշխատացնելուց միգրացիայի խնդիր որ չտա
python manage.py migrate
python manage.py collectstatic --noinput
#python manage.py loaddata main.json
python manage.py runserver 0.0.0.0:8000