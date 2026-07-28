# python-essentials-postgres-pool

PostgreSQL connection pooling with `psycopg2`'s `ThreadedConnectionPool`. Connections are borrowed and returned instead of reopened per query.

### How it works

`src/main.py` creates a `ThreadedConnectionPool(minconn=1, maxconn=5)`, seeds a `users` table, then serves 8 requests. `getconn()` borrows a connection and `putconn()` returns it. `docker-compose.yml` runs PostgreSQL 16 in podman.

### Install

```bash
./install-deps.sh
```

### Run

`start.sh` boots PostgreSQL and waits until it is ready, `test.sh` runs the whole flow, `stop.sh` tears it down.

```bash
./test.sh
```

### Output

```
request-0 rows=[(1, 'alice'), (2, 'bob'), (3, 'carol')]
request-1 rows=[(1, 'alice'), (2, 'bob'), (3, 'carol')]
...
request-7 rows=[(1, 'alice'), (2, 'bob'), (3, 'carol')]
```
