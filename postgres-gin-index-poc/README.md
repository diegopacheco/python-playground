<img src="logo.svg" alt="JSONB + GIN" width="640"/>

Lookups over a JSONB column in PostgreSQL 18, answered by GIN indexes and exposed
as a small REST API. The whole stack runs on podman-compose: PostgreSQL 18,
Liquibase applying the schema from plain SQL changelogs, and a Python 3.14.6 API.
50.003 seeded rows make the query planner choices real instead of theoretical.

## How it Works?

`start.sh` brings up PostgreSQL 18, waits until it accepts connections, then runs
Liquibase, which applies four SQL changelogs: the `documents` table, two GIN
indexes over the `data JSONB` column, the seed rows and an `ANALYZE`. Once the
schema is in place the API container starts.

The API turns query string parameters into JSONB operators. `contains` becomes
`data @> %s::jsonb`, `key` becomes `data ? %s`, `anyKey` becomes `data ?| %s`.
Those three operators are exactly what a GIN index on JSONB can serve, so the
same request that returns rows can also return its execution plan through
`/explain`, which reports which index the planner actually picked.

That last part is the point of the POC: you can see the GIN index being chosen
for a selective lookup, and see the planner correctly ignore it when a predicate
matches 5% of the table and a plain ordered scan is cheaper.

## Architecture

<img src="architecture.svg" alt="Architecture" width="1120"/>

The dashed box is what podman-compose owns. Liquibase is a one shot container: it
runs `update` against PostgreSQL and exits, so the API never starts against an
empty schema. The API talks to PostgreSQL over psycopg 3 with a small connection
pool and asks it for query plans on demand.

## Features

- **JSONB containment lookups** — `data @> {...}` matches a whole nested subtree, so filtering on `stock.warehouse` needs no extra column.
- **Key existence lookups** — `data ? key` and `data ?| [keys]` find documents by the presence of a field, which relational columns cannot express without a schema change.
- **Two GIN op classes** — `jsonb_ops` and `jsonb_path_ops` are both indexed, and the planner picks between them per query.
- **Plan introspection endpoint** — `/explain` returns `EXPLAIN (ANALYZE, BUFFERS)` plus the index names used, so index usage is proven, not assumed.
- **Schema as versioned SQL** — every table, index and seed is a Liquibase changeset, so a rerun of `start.sh` is a no-op instead of a re-create.
- **Writes are searchable immediately** — a document posted through the API is found by the GIN index in the next request, verified by `test.sh`.

## Stack

- **PostgreSQL 18** — the JSONB and GIN features under test.
- **Liquibase 4.33** — versioned schema, changesets written as plain formatted SQL rather than XML DDL.
- **Python 3.14.6** — the API runtime, matching the local interpreter.
- **psycopg 3** — the only Python dependency, with its connection pool extra.
- **http.server (stdlib)** — no web framework, the API is small enough that a framework would add more than it removes.
- **podman / podman-compose** — rootless containers for the database, migrations and API.

## Contracts / APIs

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness plus current document count |
| GET | `/documents` | Search by JSONB filters |
| GET | `/documents/{id}` | Read one document |
| GET | `/explain` | Same filters, returns the execution plan and indexes used |
| POST | `/documents` | Insert `{"name": "...", "data": { ... }}` |

Query parameters for `/documents` and `/explain`:

| Parameter | Operator | Meaning |
| --- | --- | --- |
| `contains` | `@>` | JSON object the document must contain |
| `key` | `?` | Key that must exist at the top level |
| `anyKey` | `?\|` | Comma separated keys, at least one must exist |
| `limit` | | 1 to 1000, defaults to 10 |

Search by a nested subtree:

```bash
curl -s --get http://localhost:8080/documents \
  --data-urlencode 'contains={"category":"electronics","stock":{"warehouse":"wh-1"}}'
```

```json
{
  "count": 1,
  "documents": [
    {
      "id": 1,
      "name": "laptop-x1",
      "data": {
        "sku": "SKU-LAPTOP",
        "tags": ["portable", "work"],
        "brand": "acme",
        "price": 1999.99,
        "stock": {"qty": 7, "warehouse": "wh-1"},
        "category": "electronics"
      },
      "created_at": "2026-09-01T03:06:00.884526+00:00"
    }
  ]
}
```

Prove the index answered it:

```bash
curl -s --get http://localhost:8080/explain \
  --data-urlencode 'contains={"sku":"SKU-4242"}'
```

```json
{
  "indexes": ["idx_documents_data_path_gin"],
  "ginIndexUsed": true,
  "executionTimeMs": 0.03
}
```

Insert a document:

```bash
curl -s -X POST http://localhost:8080/documents \
  -H 'Content-Type: application/json' \
  -d '{"name":"mouse-m1","data":{"sku":"SKU-MOUSE","category":"electronics","tags":["wireless"]}}'
```

## Key Data Structures and Design Decisions

The table is deliberately thin: `id`, `name`, `data JSONB`, `created_at`. Every
attribute a query filters on lives inside `data`, so the index has to do the work.

```sql
CREATE INDEX idx_documents_data_gin ON documents USING gin (data);
CREATE INDEX idx_documents_data_path_gin ON documents USING gin (data jsonb_path_ops);
```

Both op classes are indexed on purpose. `jsonb_ops` indexes keys and values, so it
serves `?` and `?|`; `jsonb_path_ops` indexes only value paths, which makes it
smaller and faster but only usable for `@>`. Keeping both lets the planner choose,
and `/explain` shows the choice it made: key existence can only use
`idx_documents_data_gin`, while containment can use either, so which one appears
depends on the cost estimate for that query.

`ORDER BY id` on the search query is a deliberate trade. It makes results stable,
and it also means that for a broad predicate the planner walks the primary key
and stops at the limit instead of using GIN. `test.sh` prints that case as an INFO
line rather than hiding it: a GIN index is for selective lookups, and PostgreSQL
skipping it when 2.500 of 50.000 rows match is the planner being right.

The seed uses `generate_series` with deterministic values, so row counts and test
assertions do not drift between runs. `ANALYZE` is its own changeset marked
`runAlways:true` and `runInTransaction:false`, because without fresh statistics
the planner has no reason to trust any index.

There is no ORM and no web framework. `db.py` builds parameterized SQL, `api.py`
routes and validates, `main.py` starts a threading HTTP server. All filter values
are bound as parameters, never interpolated.

## How to run

Create the local virtualenv with psycopg, only needed to run the API outside a
container. It uses `python3.14`, override with `PYTHON=/path/to/python`:

```bash
./install-deps.sh
```

Build the API image and pull PostgreSQL and Liquibase:

```bash
./build.sh
```

Start the stack, apply the schema and wait for the API to answer:

```bash
./start.sh
```

Run the tests against the running stack:

```bash
./test.sh
```

Stop everything:

```bash
./stop.sh
```

To run the API on the host against the containerized database instead of in a
container, use `./run.sh`, which uses `.venv` and points at `localhost:55432`.
Stop the API container first, or give it another port with `API_PORT=8081 ./run.sh`
and point the tests at it with `BASE=http://localhost:8081 ./test.sh`.

## Test output

There is no UI in this POC, the surface is the REST API. `./test.sh` is the
executable proof, each check named after the behaviour it defends:

```
the api is up and can reach postgres
PASS health reports ok
PASS the liquibase seed rows are in the table

containment @> matches a nested jsonb subtree, not a string compare
PASS only the electronics item stored in wh-1 matches
PASS the matched document is the laptop

key existence ? finds documents by the presence of a field alone
PASS only the discontinued desk has that key
PASS the matched document is the desk

any key ?| matches when at least one of the keys exists
PASS an absent key does not widen the result

the gin index is what answers a selective containment query on 50k rows
PASS planner chose a gin index
     indexes=['idx_documents_data_path_gin'] time=0.045ms

a broad predicate is cheaper without the index, the planner is free to skip it
     INFO 2500 of 50000 rows match: indexes=['documents_pkey'] time=0.054ms

the gin index also answers key existence queries
PASS planner chose a gin index
     indexes=['idx_documents_data_gin'] time=0.032ms

a document written through the api is immediately searchable by the index
PASS post returns the stored id
PASS the new document is found by containment
PASS the new document is readable by id

bad input is rejected instead of reaching the database
PASS malformed contains is a 400
PASS missing document is a 404

PASS=14 FAIL=0
TESTS OK
```
