# SQLAlchemy Async Transaction Management

A small bank running on Python 3.14.6 where the transaction boundary is a single decorator. `Controller -> Service -> DAO`,
all `async`/`await`, and `@transactional` on the service methods. If the method returns, the transaction commits. If it
raises, the whole thing rolls back. Nothing in the controller, the DAO or the models knows a session exists.

## How it Works?

`tx.py` keeps an `AsyncSession` in a `ContextVar`. When a `@transactional` method is called and the context variable is
empty, the decorator opens a session, enters `session.begin()` and stores it. When a `@transactional` method is called and
the context variable is already set, the decorator does nothing and the call joins the transaction that is already open.
That is the whole propagation rule, and it is why `transfer()` calling `withdraw()` and `deposit()` produces one
transaction instead of three.

The DAOs never receive a session as an argument. They call `current_session()`, which reads the same context variable and
raises if there is no transaction open, so a DAO can never quietly write outside a boundary. `ContextVar` is per-task, so
two concurrent requests get two independent sessions with no locking and no globals.

Commit and rollback come from `async with session.begin()`. SQLAlchemy commits on a clean exit and rolls back on any
exception, so the decorator has no `try/except` around business logic and never swallows an error.

## Architecture

![Architecture](printscreens/architecture.png)

## Features

- **One decorator marks the boundary** — `@transactional` on a service method is the only transaction code in the project.
- **Automatic propagation** — a nested `@transactional` call joins the caller's transaction instead of opening a second one.
- **Invisible session** — controller, DAO and models never take, pass or close a session; `current_session()` finds it.
- **Rollback proven against real Postgres** — the ledger row is flushed before the money moves, so a failure rolls back a write that already reached the database.
- **Task-isolated context** — `ContextVar` gives every concurrent request its own session, which a module-level session could never do.
- **Fails loud outside a boundary** — DAO access with no open transaction raises `NoActiveTransaction` instead of auto-committing.
- **Postgres 18 in podman** — the database starts, waits for readiness and stops from scripts, nothing installed on the host.

## Stack

| Piece | Why |
| --- | --- |
| Python 3.14.6 | Target runtime; the venv is built with `python3.14` explicitly. |
| SQLAlchemy 2.0 (asyncio) | Async ORM whose `session.begin()` already defines commit-or-rollback semantics. |
| psycopg 3 (binary) | Current Postgres driver with async support and wheels for 3.14. |
| `contextvars` | Standard library, task-local, the reason propagation needs no plumbing. |
| FastAPI + uvicorn | Thin async controller layer with request validation for free. |
| PostgreSQL 18 | Real transactional database; rollback has to be verified somewhere real. |
| podman + podman-compose | Runs the database without installing it. |
| pytest + pytest-asyncio | Async tests against the real database, no mocks. |

## APIs

Swagger UI is at `http://localhost:8000/docs` once the app is running.

| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| `POST` | `/api/accounts` | `{"owner": str, "initial_balance": str}` | `201` and the account. |
| `GET` | `/api/accounts` | — | All accounts. |
| `GET` | `/api/accounts/{id}` | — | One account, `404` if unknown. |
| `POST` | `/api/accounts/{id}/deposit` | `{"amount": str}` | The updated account. |
| `POST` | `/api/accounts/{id}/withdraw` | `{"amount": str}` | The updated account, `409` if funds are short. |
| `POST` | `/api/transfers` | `{"source_id": int, "target_id": int, "amount": str}` | `201` and the ledger entry. |
| `GET` | `/api/ledger` | — | All committed ledger entries. |

```bash
curl -X POST http://localhost:8000/api/transfers \
  -H 'Content-Type: application/json' \
  -d '{"source_id":1,"target_id":2,"amount":"30.00"}'
```

## Printscreens

![Swagger UI](printscreens/swagger.png)

Swagger UI at `/docs`, generated from the controller. Every route here is one `@transactional` service call: `POST
/api/transfers` runs the ledger insert, the withdrawal and the deposit inside a single transaction, and returns `409` or
`404` with the database untouched when any of the three fails.

## Key Design Decisions

**The decorator, in full.** This is the entire mechanism:

```python
def transactional[T](func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        if _current_session.get() is not None:
            return await func(*args, **kwargs)
        async with session_factory() as session:
            token = _current_session.set(session)
            try:
                async with session.begin():
                    return await func(*args, **kwargs)
            finally:
                _current_session.reset(token)
    return wrapper
```

**`ContextVar`, not a global or an argument.** A module-level session would be shared by every concurrent request. A
session argument would have to be threaded through the controller and every DAO call, which is exactly the plumbing this
POC removes. `ContextVar` is copied per asyncio task, so isolation is free.

**`reset(token)` in a `finally`.** The context variable is restored even when the body raises, so a rolled-back call
leaves nothing behind for the next call on the same task.

**The ledger row is written first, on purpose.** `transfer()` inserts the ledger entry, then withdraws, then deposits, and
every DAO write ends in `flush()`. So a failed transfer has already sent `INSERT` and `UPDATE` to Postgres before it
raises, and the rollback that follows is a real database rollback, not a discarded in-memory session. The sequence proves
it — after one committed transfer and two failed ones:

```
select last_value from ledger_id_seq;  -> 3
select count(*) from ledger;           -> 1
```

Three inserts reached the database, one survived.

**Balances are `Numeric(18, 2)`.** Money in floats is a bug, and psycopg maps `numeric` to `Decimal` in both directions.

**`expire_on_commit=False`.** The service returns ORM objects after its transaction has closed; without this the
controller would touch expired attributes on a detached instance.

## How to Run

```bash
./build.sh         # venv with python3.14 and dependencies
./start.sh         # postgres 18 in podman, then the API on http://localhost:8000
./test-client.sh   # a commit and two rollbacks over HTTP, with balances after each
./stop.sh          # api down, postgres down
```

## How to Run the Tests

```bash
./test.sh
```

`test.sh` starts Postgres and runs pytest against it. There are no mocks: the point under test is what the database does
on commit and on rollback.

```
tests/test_transaction_boundary.py::test_committed_work_is_visible_to_the_next_transaction PASSED
tests/test_transaction_boundary.py::test_transfer_commits_both_legs_and_the_ledger_together PASSED
tests/test_transaction_boundary.py::test_insufficient_funds_rolls_back_the_ledger_entry PASSED
tests/test_transaction_boundary.py::test_missing_target_rolls_back_the_debit_already_applied PASSED
tests/test_transaction_boundary.py::test_nested_service_calls_join_the_caller_transaction PASSED
tests/test_transaction_boundary.py::test_separate_service_calls_get_separate_transactions PASSED
tests/test_transaction_boundary.py::test_concurrent_transactions_do_not_share_a_session PASSED
tests/test_transaction_boundary.py::test_dao_access_without_a_transaction_is_rejected PASSED
tests/test_transaction_boundary.py::test_rollback_leaves_no_open_transaction_behind PASSED
tests/test_transaction_boundary.py::test_transaction_context_is_cleared_after_the_boundary_returns PASSED
tests/test_api.py::test_transfer_endpoint_moves_money_and_records_the_ledger PASSED
tests/test_api.py::test_failed_transfer_endpoint_leaves_the_database_untouched PASSED
tests/test_api.py::test_unknown_account_returns_not_found PASSED

13 passed
```

`test-client.sh` output, the same behaviour over HTTP:

```
--- transfer 30.00 (commits) ---
{"id":1,"owner":"alice","balance":"70.00"}
{"id":2,"owner":"bob","balance":"30.00"}
--- transfer 500.00 (rolls back, insufficient funds) ---
http 409
{"id":1,"owner":"alice","balance":"70.00"}
{"id":2,"owner":"bob","balance":"30.00"}
--- transfer to a missing account (rolls back the debit) ---
http 404
{"id":1,"owner":"alice","balance":"70.00"}
--- ledger ---
[{"id":1,"source_id":1,"target_id":2,"amount":"30.00","created_at":"..."}]
```
