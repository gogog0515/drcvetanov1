## PythonAnywhere Deploy

Target:
- `Python 3.12`
- Django app

### 1. Upload files
Upload the whole project folder to:
- `/home/<your-username>/drcvetanov`

### 2. Create virtualenv
In a Bash console on PythonAnywhere:

```bash
mkvirtualenv --python=/usr/bin/python3.12 drcvetanov-env
workon drcvetanov-env
pip install -r /home/<your-username>/drcvetanov/requirements.txt
```

### 3. Configure environment variables
In the Bash console:

```bash
echo 'export DJANGO_DEBUG=False' >> ~/.bashrc
echo 'export DJANGO_SECRET_KEY="replace-with-a-long-random-secret"' >> ~/.bashrc
echo 'export DJANGO_ALLOWED_HOSTS="<your-username>.pythonanywhere.com"' >> ~/.bashrc
echo 'export DJANGO_CSRF_TRUSTED_ORIGINS="https://<your-username>.pythonanywhere.com"' >> ~/.bashrc
source ~/.bashrc
workon drcvetanov-env
```

### 4. Create the web app
In PythonAnywhere:
- Open `Web`
- `Add a new web app`
- Choose `Manual configuration`
- Choose `Python 3.12`

### 5. Set paths in the Web tab
Virtualenv:

```text
/home/<your-username>/.virtualenvs/drcvetanov-env
```

Source code:

```text
/home/<your-username>/drcvetanov
```

### 6. Edit the WSGI file
Set it to:

```python
import os
import sys

path = '/home/<your-username>/drcvetanov'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 7. Run migrations and collect static
In Bash:

```bash
workon drcvetanov-env
cd /home/<your-username>/drcvetanov
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 8. Static files mapping
In the `Web` tab add:

URL:

```text
/static/
```

Directory:

```text
/home/<your-username>/drcvetanov/staticfiles
```

### 9. Reload
Press `Reload` in the `Web` tab.

### Notes
- SQLite is fine for a small project on PythonAnywhere.
- If you later move to MySQL or PostgreSQL, only `DATABASES` will need updating.
