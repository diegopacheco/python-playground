# python-essentials-django

Django basics in a single file: settings, URL routing, and JSON views without a full project layout.

### How it works

`src/main.py` calls `settings.configure` to set up Django in one module, defines three views (`home`, `list_tasks`, `task_detail`), wires them in `urlpatterns`, and starts the dev server with `runserver`.

### Install

```bash
./install-deps.sh
```

### Run

```bash
./run.sh
```

Then open `http://localhost:8000/`.

### Test

```bash
./test.sh
```

### Output

```
GET /            {"service": "python-essentials-django", "status": "ok"}
GET /tasks/      {"tasks": [{"id": 1, "title": "learn django", "done": false}, {"id": 2, "title": "ship poc", "done": true}]}
GET /tasks/1/    {"id": 1, "title": "learn django", "done": false}
```
