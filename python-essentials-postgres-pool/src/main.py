import os
from psycopg2 import pool

connection_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=5,
    host=os.environ.get("PG_HOST", "127.0.0.1"),
    port=int(os.environ.get("PG_PORT", "5432")),
    user=os.environ.get("PG_USER", "postgres"),
    password=os.environ.get("PG_PASSWORD", "postgres"),
    dbname=os.environ.get("PG_DATABASE", "essentials"),
)


def setup():
    conn = connection_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, name VARCHAR(50))")
        cursor.execute("DELETE FROM users")
        cursor.executemany(
            "INSERT INTO users (id, name) VALUES (%s, %s)",
            [(1, "alice"), (2, "bob"), (3, "carol")],
        )
        conn.commit()
    finally:
        connection_pool.putconn(conn)


def query_from_pool(label):
    conn = connection_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users ORDER BY id")
        rows = cursor.fetchall()
        print(f"{label} rows={rows}")
    finally:
        connection_pool.putconn(conn)


def main():
    setup()
    for i in range(8):
        query_from_pool(f"request-{i}")
    connection_pool.closeall()


if __name__ == "__main__":
    main()
