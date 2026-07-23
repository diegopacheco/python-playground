import os
from mysql.connector import pooling

config = {
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "root"),
    "database": os.environ.get("MYSQL_DATABASE", "essentials"),
}

pool = pooling.MySQLConnectionPool(pool_name="essentials_pool", pool_size=5, **config)


def setup():
    conn = pool.get_connection()
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
        conn.close()


def query_from_pool(label):
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users ORDER BY id")
        rows = cursor.fetchall()
        print(f"{label} pool_size={pool.pool_size} rows={rows}")
    finally:
        conn.close()


def rename_in_transaction(changes):
    conn = pool.get_connection()
    try:
        conn.start_transaction()
        cursor = conn.cursor()
        cursor.executemany("UPDATE users SET name = %s WHERE id = %s", changes)
        conn.commit()
        print(f"transaction committed changes={changes}")
    except Exception as error:
        conn.rollback()
        print(f"transaction rolled back error={error}")
    finally:
        conn.close()


def failing_transaction():
    conn = pool.get_connection()
    try:
        conn.start_transaction()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET name = %s WHERE id = %s", ("temp", 1))
        cursor.execute("INSERT INTO users (id, name) VALUES (%s, %s)", (2, "duplicate"))
        conn.commit()
        print("transaction committed")
    except Exception as error:
        conn.rollback()
        print(f"transaction rolled back error={error}")
    finally:
        conn.close()


def main():
    setup()
    for i in range(8):
        query_from_pool(f"request-{i}")
    rename_in_transaction([("alice2", 1), ("bob2", 2)])
    query_from_pool("after-commit")
    failing_transaction()
    query_from_pool("after-rollback")


if __name__ == "__main__":
    main()
