# python-essentials-pgvector

Vector similarity search inside PostgreSQL using the `pgvector` extension: store embeddings as a `vector` column and query nearest neighbors with SQL.

### What it does

`src/main.py` enables the `vector` extension, creates an `items` table with a `vector(3)` column, inserts a few labeled vectors, then runs nearest-neighbor queries with both cosine distance (`<=>`) and L2 distance (`<->`) directly in SQL. PostgreSQL with pgvector runs in a podman container.

### Features

- `pgvector` extension in PostgreSQL 16
- `vector` typed column
- Cosine (`<=>`), L2 (`<->`), and inner-product (`<#>`) distance operators
- `ORDER BY distance LIMIT k` nearest-neighbor search
- numpy vectors bound through `register_vector`

### Stack

- Python 3.14.6
- psycopg2 + pgvector (Python)
- numpy
- pgvector/pgvector:pg16 (podman)

### Architecture

`test.sh` -> `start.sh` boots the pgvector image in podman -> `src/main.py` creates the extension and table, inserts vectors, and issues `ORDER BY embedding <=> query` -> PostgreSQL ranks rows by vector distance and returns the nearest names.

### Install

```bash
./install-deps.sh
```

### Run

`start.sh` boots PostgreSQL, `test.sh` runs the whole flow, `stop.sh` tears it down.

```bash
./test.sh
```

### Output

```
postgres ready
query vector: [1.0, 0.1, 0.0]
nearest by cosine distance (<=>):
  apple: 0.0000
  orange: 0.0030
  banana: 0.0129
nearest by L2 distance (<->):
  apple: 0.0000
  orange: 0.0866
  banana: 0.1732
```
