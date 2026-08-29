# SQLAlchemy Async Transaction Management

A small bank running on Python 3.14.6 where the transaction boundary is a single decorator. `Controller -> Service -> DAO`,
all `async`/`await`, and `@transactional` on the service methods. If the method returns, the transaction commits. If it
raises, the whole thing rolls back. Nothing in the controller, the DAO or the models knows a session exists.

## How it Works?

`tx.py` keeps an `AsyncSession` in a `ContextVar`. When a `@transactional` method is called and the context variable is
empty, the decorator opens a session, enters `session.begin()` and stores it. When a `@transactional` method is called and
the context variable is already set, the decorator does nothing and the call joins the transaction that is already open.
That is the whole propagation rule, and it is why `BankService.transfer()` calling `LedgerService.record()` and then its
own `withdraw()` and `deposit()` produces one transaction instead of four.

A joined call that raises also marks the transaction rollback-only, so a caller that catches the exception still cannot
commit half the work. That is Spring's participation behaviour, and it is what `UnexpectedRollback` is for. The catch is
`except BaseException`, not `except Exception`, because `asyncio.CancelledError` is not an `Exception`: a joined call
killed by `asyncio.timeout()` has to poison the transaction like any other failure, or a swallowed `TimeoutError` commits
half a transfer. The context remembers the exception that poisoned it, so `UnexpectedRollback.__cause__` names the
original failure, and an exception that is simply propagating out of the boundary is re-raised untouched instead of
being masked.

The DAOs never receive a session as an argument. They call `current_session()`, which reads the same context variable and
raises if there is no transaction open, so a DAO can never quietly write outside a boundary. `ContextVar` is per-task, so
two concurrent requests get two independent sessions with no locking and no globals.

Per-task is also enforced, not just assumed. A `ContextVar` is *copied* into every task spawned inside the boundary, so
an `asyncio.create_task()` or an `asyncio.gather()` of service calls would inherit the caller's `AsyncSession` and drive
it from two tasks at once, which SQLAlchemy does not allow. Each context therefore records the task that opened it, and a
lookup from any other task raises `CrossTaskTransaction` instead of corrupting the session or, worse, silently splitting
one transaction into several.

Commit and rollback themselves come from `async with session.begin()`. SQLAlchemy commits on a clean exit and rolls back
on any exception, so the decorator has no `try/except` around business logic and never swallows an error.

## Architecture

![Architecture](printscreens/architecture.png)

## Features

- **One decorator marks the boundary** — `@transactional` on a service method is the only transaction code in the project.
- **Automatic propagation** — a nested call, including a call into a different service, joins the caller's transaction instead of opening a second one.
- **Rollback-only participation** — a failed joined call poisons the transaction, so swallowing the exception cannot produce a half-committed transfer.
- **Contention handled with row locks** — `SELECT ... FOR UPDATE` serialises the read-modify-write per account, so concurrent deposits cannot lose updates.
- **Deadlock-free by lock ordering** — a transfer locks both accounts in ascending id order, so opposite transfers cannot each hold what the other needs.
- **Invisible session** — controller, DAO and models never take, pass or close a session; `current_session()` finds it.
- **Rollback proven against real Postgres** — the ledger row is flushed before the money moves, so a failure rolls back a write that already reached the database.
- **The database enforces it too** — `CHECK (balance >= 0)` and foreign keys from `ledger` to `accounts`, so a bug in the service cannot leave a negative balance or an orphan ledger row behind.
- **Bounded waiting** — `lock_timeout` and `statement_timeout` are set on every connection, so a stalled transaction cannot block a hot account forever; the wait surfaces as `503` rather than a hang.
- **Frozen views cross the boundary** — the service returns dataclasses, never ORM entities, so nothing detached ever reaches the controller.
- **Task-isolated context** — `ContextVar` gives every concurrent request its own session, and a task spawned inside a boundary is refused that session rather than sharing it.
- **Cancellation is a rollback** — a joined call killed by a timeout poisons the transaction, so a caller that swallows the `TimeoutError` still cannot commit.
- **Fails loud outside a boundary** — DAO access with no open transaction raises `NoActiveTransaction` instead of auto-committing.
- **UI that shows the boundary** — every action prints COMMIT or ROLLBACK with the balances before and after.
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
| Plain HTML, CSS and `fetch` | The UI is one self-contained file, no framework and no build step. |

## APIs

The UI is at `http://localhost:8000/` and Swagger UI at `http://localhost:8000/docs`.

| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| `GET` | `/` | — | The UI. |
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

## Is this the same as Spring @Transactional?

For the default Spring settings, yes on everything that matters. The differences are listed honestly below.

| Behaviour | Spring | Here |
| --- | --- | --- |
| Default propagation | `REQUIRED` | `REQUIRED`, the only mode implemented |
| Commit | method returns | method returns |
| Rollback | unchecked exceptions only | any exception; Python has no checked exceptions |
| Joined call fails, caller swallows it | rollback-only, then `UnexpectedRollbackException` | rollback-only, then `UnexpectedRollback` |
| Nested call opens a second transaction | no, it joins | no, it joins |
| Self-invocation | bypasses the proxy, so no transaction at all | still participates; the decorator wraps the function itself |
| Transaction is bound to | the thread (`ThreadLocal`) | the asyncio task (`ContextVar`) |
| Joined call cancelled, caller swallows it | rollback-only | rollback-only, `CancelledError` is not an `Exception` but is still caught |
| Transaction reused from another thread/task | `ThreadLocal`, so a new thread simply has none | `CrossTaskTransaction`, a spawned task is refused the inherited session |
| `REQUIRES_NEW`, `NESTED`, `SUPPORTS`, `MANDATORY` | supported | not implemented |
| `readOnly`, `isolation`, `timeout` | supported | not implemented |

Two of those deserve a sentence.

**Self-invocation is where this beats Spring.** Spring's `@Transactional` is a proxy, so `this.withdraw()` inside
`transfer()` never reaches it, which is the framework's most famous gotcha. Here the decorator wraps the function object,
so a self-call participates like any other call. With `REQUIRED` the observable result is the same whenever the outer
method is itself transactional, and strictly safer when it is not.

**Rollback rules are simpler on purpose.** Spring distinguishes checked from unchecked exceptions because Java has both.
Python does not, so every exception rolls back, which is what `rollbackFor = Exception.class` gives you in Java anyway.

The propagation claims are not assertions in prose; they are what `tests/test_transaction_boundary.py` checks by
capturing the session object at each layer and comparing identities.

## Race Conditions and Contention

A correct transaction boundary does **not** make a bank safe. `withdraw()` reads the balance, changes it in Python and
writes it back, and two of those interleaving lose one of the writes. The boundary commits both, faithfully, and the
money is still wrong. This is what the contention suite is for, and it is worth seeing it fail. With the
`SELECT ... FOR UPDATE` removed and nothing else changed:

```
$ .venv/bin/python -m pytest tests/test_contention.py -q

FAILED test_concurrent_deposits_do_not_lose_updates
        assert Decimal('20.00') == Decimal('100.00')
FAILED test_transfers_in_opposite_directions_do_not_deadlock
        assert Decimal('240.00') == Decimal('200.00')
FAILED test_money_is_conserved_under_concurrent_transfers

3 failed, 3 passed in 6.61s
```

Ten concurrent deposits of `10.00` into an empty account left `20.00` in it: eight writes were lost. Ten transfers
running in both directions between two accounts turned `200.00` into `240.00`: the bank invented money. The 6.61s
runtime is Postgres deadlock detection firing, because without a lock order `alice -> bob` and `bob -> alice` each hold
the row the other one wants. As shipped, the same file runs in 0.42s with six passes.

Two changes fix it, both in the service and DAO, none in `tx.py`:

**`SELECT ... FOR UPDATE` on every read that is about to write.** `AccountDAO.find_for_update()` locks the row, so a
second transaction reading the same account blocks until the first one commits or rolls back, and then reads the value
that actually won. `populate_existing=True` makes SQLAlchemy overwrite whatever the identity map was holding, so the
locked row is the row the code reasons about.

**Ascending lock order in `transfer()`.** Before moving anything, `transfer()` locks both accounts in one
`WHERE id IN (...) ORDER BY id FOR UPDATE`. Postgres puts its `LockRows` node above the `Sort`, so the rows are locked
in ascending id order, and two opposite transfers queue on the same first row instead of grabbing one each and waiting
forever.

What the suite checks, all automated in `tests/test_contention.py`:

| Test | What would break without the fix |
| --- | --- |
| `test_concurrent_withdrawals_cannot_overdraw_the_account` | 10 concurrent full-balance withdrawals; exactly one wins, nine get `InsufficientFunds`, balance lands on `0.00`, never negative. |
| `test_concurrent_deposits_do_not_lose_updates` | 10 concurrent deposits must all land. Caught the lost update. |
| `test_transfers_in_opposite_directions_do_not_deadlock` | 10 transfers alternating direction between two accounts; no exception and the total is unchanged. Caught the deadlock and the invented money. |
| `test_money_is_conserved_under_concurrent_transfers` | 12 concurrent transfers around 4 accounts; the total is conserved, at least one commits, every refusal is `InsufficientFunds` and the ledger holds exactly one row per commit. |
| `test_propagation_holds_under_concurrency` | 4 concurrent transfers; every layer inside one transfer shares one session, and the 4 transfers use 4 different sessions. Propagation and isolation at the same time. |
| `test_a_rolled_back_insert_really_reached_the_database` | `ledger_id_seq` advances on a failed transfer while the row count does not, proving Postgres rolled back a real write. |

Honest limits, since this is a POC and not a payment system:

- Isolation is Postgres' default `READ COMMITTED`. The row locks are what make the balance arithmetic safe, not the isolation level.
- Nothing retries. A transaction that Postgres aborts, for a deadlock it detects through some other access pattern or for a serialization failure, surfaces as an error to the caller instead of being replayed.
- Rollback-only survives a swallowed database error, but only as a diagnosis. Once Postgres aborts the transaction there is nothing left to continue with, because there are no savepoints; the caller gets `UnexpectedRollback` with the driver error as its cause instead of a confusing SQLAlchemy state error.
- `withdraw()` and `deposit()` re-lock the row they were handed, because both are callable on their own and have to be safe that way. A transfer therefore spends six round trips where four would do. The redundant locks are already held, so they cost latency and never risk.
- The lock is per account row, so unrelated accounts never block each other, but a hot account serialises every transfer that touches it. That is the intended trade: correctness first.
- The schema is `create_all`, not migrations. The constraints are DDL, so a database created before them keeps the old shape; `podman-compose down -v` once is what applies them to an existing volume.

## Key Design Decisions

**The decorator, in full.** This is the entire mechanism:

```python
def transactional[T](func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        joined = _active()
        if joined is not None:
            try:
                return await func(*args, **kwargs)
            except BaseException as error:
                if joined.failure is None:
                    joined.failure = error
                raise
        async with session_factory() as session:
            context = TransactionContext(session, asyncio.current_task())
            token = _current.set(context)
            try:
                async with session.begin():
                    try:
                        result = await func(*args, **kwargs)
                    except BaseException as error:
                        if context.failure is not None and error is not context.failure:
                            raise UnexpectedRollback(ROLLBACK_ONLY) from error
                        raise
                    if context.failure is not None:
                        raise UnexpectedRollback(ROLLBACK_ONLY) from context.failure
                    return result
            finally:
                _current.reset(token)
    return wrapper
```

**`ContextVar`, not a global or an argument.** A module-level session would be shared by every concurrent request. A
session argument would have to be threaded through the controller and every DAO call, which is exactly the plumbing this
POC removes. `ContextVar` is copied per asyncio task, so isolation is free.

**`reset(token)` in a `finally`.** The context variable is restored even when the body raises, so a rolled-back call
leaves nothing behind for the next call on the same task.

**Two services, one boundary.** `BankService.transfer()` calls `LedgerService.record()`, a different class with its own
`@transactional` methods. Called on its own, `LedgerService.record()` opens and commits its own transaction. Called from
`transfer()`, it joins. Neither service knows which of the two is happening, which is the point.

**The ledger row is written before the money moves, on purpose.** `transfer()` locks both accounts, records the ledger
entry, then withdraws and deposits, and every DAO write ends in `flush()`. So a failed transfer has already sent
`INSERT` and `UPDATE` to Postgres before it raises, and the rollback that follows is a real database rollback, not a
discarded in-memory session. The locks come first because they are what proves both accounts exist: a missing account
has to fail as `AccountNotFound` and a `404`, not as a foreign key violation. The sequence proves
it — after one committed transfer and two failed ones:

```
select last_value from ledger_id_seq;  -> 3
select count(*) from ledger;           -> 1
```

Three inserts reached the database, one survived.

**Balances are `Numeric(18, 2)`.** Money in floats is a bug, and psycopg maps `numeric` to `Decimal` in both directions.

**Views cross the boundary, entities do not.** A service method returns a frozen `AccountView` or `LedgerView` built
while the transaction is still open, not the ORM entity. An entity handed to the controller is detached the moment the
session closes, so any attribute the session had not already loaded raises `DetachedInstanceError` — today that would
be nothing, because the models have no relationships and Postgres returns `created_at` from the `INSERT`, but it is a
trap set for the first relationship anyone adds. Because the reads happen inside the boundary, `expire_on_commit` is
left at its default instead of being switched off to paper over the problem.

**`lock_timeout` and `statement_timeout` on every connection.** Row locks make a hot account serialise, which is the
intended trade, but without a timeout a single stalled transaction blocks every transfer touching that account
indefinitely. Five seconds to acquire a lock and fifteen for a statement turn that into an error the caller can see.

## Printscreens

### Bank

![Bank tab](printscreens/ui-bank.png)

Four service calls, top to bottom in the log. `open_account("dave", 0.00)` and `transfer(6 -> 7, 30.00)` committed, so
carol is down to 70.00 and dave holds 30.00. Then `transfer(6 -> 7, 5000.00)` failed on insufficient funds: the log
prints the balances before and after and they are identical, and no ledger row appeared even though one had already been
inserted and flushed. `withdraw(7, 9999.00)` failed the same way. The account table is the state Postgres actually holds,
re-read after every call.

### How it works

![How it works tab](printscreens/ui-how.png)

The decorator and the `transfer()` method with line numbers, annotated line by line: where propagation is decided, where
rollback-only is set, where the boundary opens, and where the commit is refused. Below them the contention card shows
the `FOR UPDATE` lock and the ascending lock order with the numbers from the failing run, and the last card is the
Spring comparison table above.

### Swagger

![Swagger UI](printscreens/swagger.png)

Swagger UI at `/docs`, generated from the controller. Every route here is exactly one `@transactional` service call.

## How to Run

```bash
./build.sh         # venv with python3.14 and dependencies
./start.sh         # postgres 18 in podman, then the app on http://localhost:8000
./test-client.sh   # a commit and two rollbacks over HTTP, with balances after each
./test.sh          # 29 tests against a real postgres, in a separate database
./stop.sh          # app down, postgres down
```

## How to Run the Tests

```bash
./test.sh
```

`test.sh` starts Postgres and runs pytest against it. There are no mocks: the point under test is what the database does
on commit and on rollback.

The suite drops and recreates the schema between tests, so it runs against `bank_test_db`, a second database that
`db-start.sh` creates next to `bank_db`. Running the tests therefore never touches the data the app is holding. `tests/conftest.py`
sets that URL before importing anything, and `TEST_DATABASE_URL` overrides it.

```
tests/test_api.py::test_transfer_endpoint_moves_money_and_records_the_ledger PASSED
tests/test_api.py::test_failed_transfer_endpoint_leaves_the_database_untouched PASSED
tests/test_api.py::test_unknown_account_returns_not_found PASSED
tests/test_contention.py::test_concurrent_withdrawals_cannot_overdraw_the_account PASSED
tests/test_contention.py::test_concurrent_deposits_do_not_lose_updates PASSED
tests/test_contention.py::test_transfers_in_opposite_directions_do_not_deadlock PASSED
tests/test_contention.py::test_money_is_conserved_under_concurrent_transfers PASSED
tests/test_contention.py::test_propagation_holds_under_concurrency PASSED
tests/test_contention.py::test_a_rolled_back_insert_really_reached_the_database PASSED
tests/test_transaction_boundary.py::test_committed_work_is_visible_to_the_next_transaction PASSED
tests/test_transaction_boundary.py::test_transfer_commits_both_legs_and_the_ledger_together PASSED
tests/test_transaction_boundary.py::test_insufficient_funds_rolls_back_the_ledger_entry PASSED
tests/test_transaction_boundary.py::test_missing_target_is_refused_before_any_row_is_written PASSED
tests/test_transaction_boundary.py::test_nested_service_calls_join_the_caller_transaction PASSED
tests/test_transaction_boundary.py::test_separate_service_calls_get_separate_transactions PASSED
tests/test_transaction_boundary.py::test_concurrent_transactions_do_not_share_a_session PASSED
tests/test_transaction_boundary.py::test_dao_access_without_a_transaction_is_rejected PASSED
tests/test_transaction_boundary.py::test_rollback_leaves_no_open_transaction_behind PASSED
tests/test_transaction_boundary.py::test_transaction_context_is_cleared_after_the_boundary_returns PASSED
tests/test_transaction_boundary.py::test_call_into_another_service_joins_the_same_transaction PASSED
tests/test_transaction_boundary.py::test_the_other_service_opens_its_own_transaction_when_called_alone PASSED
tests/test_transaction_boundary.py::test_a_failure_swallowed_by_the_caller_still_rolls_the_transaction_back PASSED
tests/test_transaction_boundary.py::test_rollback_only_does_not_leak_into_the_next_transaction PASSED
tests/test_transaction_boundary.py::test_a_cancelled_joined_call_cannot_commit_its_partial_work PASSED
tests/test_transaction_boundary.py::test_a_swallowed_database_error_cannot_be_committed_over PASSED
tests/test_transaction_boundary.py::test_a_spawned_task_cannot_borrow_the_callers_session PASSED
tests/test_transaction_boundary.py::test_a_transfer_to_the_same_account_is_rejected PASSED
tests/test_transaction_boundary.py::test_the_ledger_cannot_reference_an_account_that_does_not_exist PASSED
tests/test_transaction_boundary.py::test_the_schema_refuses_a_negative_balance PASSED

29 passed
```
