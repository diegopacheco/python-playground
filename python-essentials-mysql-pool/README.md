# python-essentials-mysql-pool

MySQL connection pooling with `mysql-connector-python`. A fixed pool of 5 connections is reused across many requests instead of opening a new one each time.

### How it works

`src/main.py` builds a `MySQLConnectionPool(pool_size=5)`, seeds a `users` table, then serves 8 requests. Each `get_connection()` borrows a pooled connection and `close()` returns it to the pool. `docker-compose.yml` runs MySQL 8.4 in podman.

### Install

```bash
./install-deps.sh
```

### Run

`start.sh` boots MySQL and waits until it is ready, `test.sh` runs the whole flow, `stop.sh` tears it down.

```bash
./test.sh
```

### Output

```
request-0 pool_size=5 rows=[(1, 'alice'), (2, 'bob'), (3, 'carol')]
request-1 pool_size=5 rows=[(1, 'alice'), (2, 'bob'), (3, 'carol')]
...
request-7 pool_size=5 rows=[(1, 'alice'), (2, 'bob'), (3, 'carol')]
```
