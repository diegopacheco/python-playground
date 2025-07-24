### Rationale

1. Generate 10k unique IDs.
2. Store them in a JSON file.
3. Load the IDs into memory using a Map when server bootup.
4. Do a HashMap lookup for each ID.

### Performance Benchmarks

10k
```bash
❯ ./run.sh
Loaded 10000 IDs into memory in 2.49 milliseconds
Operations to perform:
  Apply all migrations: auth, contenttypes
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
Loaded 10000 IDs into memory in 2.73 milliseconds
Loaded 10000 IDs into memory in 2.64 milliseconds
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
July 24, 2025 - 03:58:26
Django version 5.2.4, using settings 'ids_checker.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.

WARNING: This is a development server. Do not use it in a production setting. Use a production WSGI or ASGI server instead.
For more information on production servers see: https://docs.djangoproject.com/en/5.2/howto/deployment/
ID check took 0.0072 milliseconds
[24/Jul/2025 03:58:40] "GET /check/04317129-1eb7-4ed4-9cd0-86043412c45f HTTP/1.1" 200 25
ID check took 0.0064 milliseconds
[24/Jul/2025 03:58:40] "GET /check/99999999-9999-9999-9999-999999999999 HTTP/1.1" 200 33
```

100k
```bash
❯ ./run.sh
Loaded 100000 IDs into memory in 26.26 milliseconds
Operations to perform:
  Apply all migrations: auth, contenttypes
Running migrations:
  No migrations to apply.
Loaded 100000 IDs into memory in 27.64 milliseconds
Loaded 100000 IDs into memory in 30.83 milliseconds
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
July 24, 2025 - 03:59:43
Django version 5.2.4, using settings 'ids_checker.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.

WARNING: This is a development server. Do not use it in a production setting. Use a production WSGI or ASGI server instead.
For more information on production servers see: https://docs.djangoproject.com/en/5.2/howto/deployment/
ID check took 0.0072 milliseconds
[24/Jul/2025 03:59:48] "GET /check/04317129-1eb7-4ed4-9cd0-86043412c45f HTTP/1.1" 200 33
ID check took 0.0055 milliseconds
[24/Jul/2025 03:59:48] "GET /check/99999999-9999-9999-9999-999999999999 HTTP/1.1" 200 33
```