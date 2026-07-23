# python-essentials-sqlalchemy

SQLAlchemy 2.0 ORM over an in-memory SQLite database: declarative models, a one-to-many relationship, inserts, queries, filters, joins, and updates.

### How it works

`src/main.py` defines `Author` and `Book` with `Mapped` columns and a `relationship`, creates the schema, inserts authors with their books, then runs `select` queries with `order_by`, `like`, relationship access, and an update.

### Install

```bash
./install-deps.sh
```

### Run

```bash
./run.sh
```

### Output

```
all books:
  Clean Architecture by Robert Martin
  Clean Code by Robert Martin
  Refactoring by Martin Fowler
filter title like Clean%:
  Clean Code
  Clean Architecture
join count per author:
  Robert Martin: 2 book(s)
  Martin Fowler: 1 book(s)
after update: Refactoring 2nd Edition
```
