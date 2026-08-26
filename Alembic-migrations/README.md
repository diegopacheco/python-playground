# Alembic Migrations

Alembic schema migrations against PostgreSQL 17 running on Podman.

## Stack

* PostgreSQL 17 (Podman container `alembic_postgres`)
* Alembic 1.16.5
* psycopg 3 (binary)

## Layout

```
alembic.ini                            alembic config + database url
docker-compose.yml                     postgres container
migrations/env.py                      alembic runtime
migrations/versions/0001_create_teams.py
migrations/versions/0002_create_members.py
```

## Schema

`0001` creates `teams`, `0002` creates `members` with a foreign key to `teams`.

## Build

```bash
./build.sh
```

Creates `.venv` and installs `requirements.txt`.

```
build done
```

## Run

```bash
./run.sh
```

Starts PostgreSQL, waits until it accepts connections, applies all migrations.

```
Waiting for PostgreSQL to be ready...
PostgreSQL is ready
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, create teams
INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002, create members
0002 (head)
```

## Test

```bash
./test.sh
```

Checks both tables, the foreign key and the version marker, then downgrades to `0001`, verifies `members` is gone and `teams` survived, and upgrades back to head.

```
PASS: teams table exists
PASS: members table exists
PASS: members has team foreign key
PASS: version is 0002
PASS: downgrade drops members
PASS: downgrade keeps teams
PASS: re-upgrade restores members
all tests passed
```

## Stop

```bash
./stop.sh
```

## Adding a migration

```bash
.venv/bin/alembic revision -m "create projects"
.venv/bin/alembic upgrade head
```

## Connection

```
host     localhost
port     5432
database alembic_db
user     alembic_user
password alembic_pass
```

```bash
podman exec -it alembic_postgres psql -U alembic_user -d alembic_db
```
