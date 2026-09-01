import json
import os

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

CONNINFO = " ".join(
    [
        f"host={os.getenv('DB_HOST', 'localhost')}",
        f"port={os.getenv('DB_PORT', '55432')}",
        f"dbname={os.getenv('DB_NAME', 'ginpoc')}",
        f"user={os.getenv('DB_USER', 'poc')}",
        f"password={os.getenv('DB_PASSWORD', 'poc')}",
    ]
)

SELECT_COLUMNS = "id, name, data, created_at"

pool = ConnectionPool(CONNINFO, min_size=1, max_size=8, open=False)


def start():
    pool.open()
    pool.wait(timeout=30)


def stop():
    pool.close()


def build_filter(contains, has_key, has_any_key):
    clauses = []
    params = []
    if contains is not None:
        clauses.append("data @> %s::jsonb")
        params.append(json.dumps(contains))
    if has_key:
        clauses.append("data ? %s")
        params.append(has_key)
    if has_any_key:
        clauses.append("data ?| %s")
        params.append(has_any_key)
    where = " AND ".join(clauses) if clauses else "TRUE"
    return where, params


def search(contains, has_key, has_any_key, limit):
    where, params = build_filter(contains, has_key, has_any_key)
    query = f"SELECT {SELECT_COLUMNS} FROM documents WHERE {where} ORDER BY id LIMIT %s"
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params + [limit])
        return cur.fetchall()


def explain(contains, has_key, has_any_key, limit):
    where, params = build_filter(contains, has_key, has_any_key)
    query = (
        f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) "
        f"SELECT {SELECT_COLUMNS} FROM documents WHERE {where} ORDER BY id LIMIT %s"
    )
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(query, params + [limit])
        plan = cur.fetchone()[0][0]
    return plan


def indexes_used(plan_node, found=None):
    found = [] if found is None else found
    name = plan_node.get("Index Name")
    if name and name not in found:
        found.append(name)
    for child in plan_node.get("Plans", []):
        indexes_used(child, found)
    return found


def by_id(document_id):
    query = f"SELECT {SELECT_COLUMNS} FROM documents WHERE id = %s"
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, [document_id])
        return cur.fetchone()


def insert(name, data):
    query = (
        f"INSERT INTO documents (name, data) VALUES (%s, %s::jsonb) "
        f"RETURNING {SELECT_COLUMNS}"
    )
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, [name, json.dumps(data)])
        return cur.fetchone()


def count():
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM documents")
        return cur.fetchone()[0]
