import os

import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector

DOCS = [
    ("apple", [1.00, 0.10, 0.00]),
    ("orange", [0.95, 0.15, 0.05]),
    ("banana", [0.90, 0.20, 0.10]),
    ("car", [0.05, 0.10, 0.95]),
    ("truck", [0.10, 0.05, 0.90]),
]


def connect():
    return psycopg2.connect(
        host=os.environ.get("PG_HOST", "127.0.0.1"),
        port=int(os.environ.get("PG_PORT", "5432")),
        user=os.environ.get("PG_USER", "postgres"),
        password=os.environ.get("PG_PASSWORD", "postgres"),
        dbname=os.environ.get("PG_DATABASE", "essentials"),
    )


def main() -> None:
    conn = connect()
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)

    cur.execute("DROP TABLE IF EXISTS items")
    cur.execute("CREATE TABLE items (id serial PRIMARY KEY, name text, embedding vector(3))")
    for name, embedding in DOCS:
        cur.execute(
            "INSERT INTO items (name, embedding) VALUES (%s, %s)",
            (name, np.array(embedding)),
        )

    query = np.array([1.0, 0.1, 0.0])
    print("query vector:", query.tolist())

    print("nearest by cosine distance (<=>):")
    cur.execute(
        "SELECT name, embedding <=> %s AS distance FROM items ORDER BY distance LIMIT 3",
        (query,),
    )
    for name, distance in cur.fetchall():
        print(f"  {name}: {distance:.4f}")

    print("nearest by L2 distance (<->):")
    cur.execute(
        "SELECT name, embedding <-> %s AS distance FROM items ORDER BY distance LIMIT 3",
        (query,),
    )
    for name, distance in cur.fetchall():
        print(f"  {name}: {distance:.4f}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
