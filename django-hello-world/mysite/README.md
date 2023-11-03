### Install Django
```bash
python -m pip install Django
```

### Create Project
```
django-admin startproject mysite
```

### Run
```bash
python manage.py runserver
```
goto http://127.0.0.1:8000/

### Admin interface

create a user
```bash
python manage.py migrate
python manage.py createsuperuser
```

goto: http://127.0.0.1:8000/admin/