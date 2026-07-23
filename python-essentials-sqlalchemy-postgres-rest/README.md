# python-essentials-sqlalchemy-postgres-rest

A REST API backed by PostgreSQL through the SQLAlchemy 2.0 ORM, served by FastAPI with an auto-generated Swagger UI.

### What it does

Exposes CRUD endpoints for a `books` table. PostgreSQL runs in a podman container, SQLAlchemy maps the `Book` model and creates the schema on startup, and FastAPI serves the endpoints plus interactive docs at `/docs`.

### Features

- SQLAlchemy 2.0 declarative model with typed `Mapped` columns
- PostgreSQL 16 running in podman
- FastAPI REST endpoints: create, list, get, delete
- Swagger UI at `/docs`, OpenAPI schema at `/openapi.json`
- Pydantic request and response models
- `test.sh` drives the whole flow end to end

### Stack

- Python 3.14.6
- SQLAlchemy + psycopg2
- FastAPI + uvicorn
- PostgreSQL 16 (podman)

### Architecture

`test.sh` -> `start.sh` boots PostgreSQL in podman and launches uvicorn -> FastAPI receives HTTP requests -> SQLAlchemy `Session` reads and writes the `books` table in PostgreSQL -> JSON responses returned to the client.

### Endpoints

- `GET /health`
- `POST /books` `{ "title": "...", "author": "..." }`
- `GET /books`
- `GET /books/{id}`
- `DELETE /books/{id}`
- `GET /docs` (Swagger UI)

### Install

```bash
./install-deps.sh
```

### Run

`start.sh` boots PostgreSQL and the API, `test.sh` runs the whole flow, `stop.sh` tears it down.

```bash
./test.sh
```

To run only the API against a running database:

```bash
./run.sh
```

### Output

```
postgres ready
api ready
--- create ---
{"title":"Clean Code","author":"Robert Martin","id":1}
{"title":"Refactoring","author":"Martin Fowler","id":2}
--- list ---
[{"title":"Clean Code","author":"Robert Martin","id":1},{"title":"Refactoring","author":"Martin Fowler","id":2}]
--- get 1 ---
{"title":"Clean Code","author":"Robert Martin","id":1}
--- delete 1 ---
{"deleted":1}
--- list after delete ---
[{"title":"Refactoring","author":"Martin Fowler","id":2}]
--- swagger ui ---
GET /docs -> 200
```
