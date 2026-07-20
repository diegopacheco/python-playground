# python-essentials-flask-rest

A Flask REST API exposing every verb: `GET`, `POST`, `PUT`, `PATCH`, `DELETE` over an in-memory book store.

### How it works

`src/main.py` maps each verb to a route. `GET /books` lists, `GET /books/<id>` reads one, `POST /books` creates, `PUT` replaces, `PATCH` partially updates, and `DELETE` removes. Missing ids return 404.

### Install

```bash
./install-deps.sh
```

### Run

```bash
./run.sh
```

### Test

`test.sh` starts the server and calls each verb with `curl`.

```bash
./test.sh
```

### Output

```
GET all      [{"author":"Robert Martin","id":1,"title":"Clean Code"}]
POST create  {"author":"Hunt","id":2,"title":"The Pragmatic Programmer"}
GET one      {"author":"Hunt","id":2,"title":"The Pragmatic Programmer"}
PUT replace  {"author":"Fowler","id":2,"title":"Refactoring"}
PATCH update {"author":"Martin Fowler","id":2,"title":"Refactoring"}
DELETE       {"deleted":{"author":"Martin Fowler","id":2,"title":"Refactoring"}}
```
