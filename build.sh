#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py migrate
python appointments/scripts/create_superuser.py
python manage.py collectstatic --noinput
