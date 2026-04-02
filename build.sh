#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py migrate
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.getenv('DJANGO_SUPERUSER_USERNAME')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
email = os.getenv('DJANGO_SUPERUSER_EMAIL', '')
if username and password:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': email, 'is_staff': True, 'is_superuser': True},
    )
    user.is_staff = True
    user.is_superuser = True
    if email:
        user.email = email
    user.set_password(password)
    user.save()
    print('superuser ok')
else:
    print('superuser skipped')
"
python manage.py collectstatic --noinput
