import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402


def main():
    username = os.getenv("DJANGO_SUPERUSER_USERNAME")
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
    email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")

    if not username or not password:
        print("Skipping superuser creation: missing env vars.")
        return

    user_model = get_user_model()
    user, created = user_model.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_staff": True,
            "is_superuser": True,
        },
    )

    user.is_staff = True
    user.is_superuser = True
    if email:
        user.email = email
    user.set_password(password)
    user.save()

    print("Superuser created." if created else "Superuser updated.")


if __name__ == "__main__":
    main()
