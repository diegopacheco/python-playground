import asyncio
import inspect
import re
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import controller
import service as service_module
import tx
from controller import app
from dao import AccountDAO
from db import DATABASE_URL, TIMEOUTS
from service import BankService, InsufficientFunds
from tx import current_session, transactional


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://bank") as client:
        yield client


async def test_transfer_endpoint_moves_money_and_records_the_ledger(
    client: httpx.AsyncClient,
):
    source = await client.post(
        "/api/accounts", json={"owner": "alice", "initial_balance": "100.00"}
    )
    target = await client.post(
        "/api/accounts", json={"owner": "bob", "initial_balance": "0.00"}
    )
    source_id = source.json()["id"]
    target_id = target.json()["id"]

    response = await client.post(
        "/api/transfers",
        json={"source_id": source_id, "target_id": target_id, "amount": "25.00"},
    )

    assert response.status_code == 201
    assert (await client.get(f"/api/accounts/{source_id}")).json()["balance"] == "75.00"
    assert (await client.get(f"/api/accounts/{target_id}")).json()["balance"] == "25.00"
    assert len((await client.get("/api/ledger")).json()) == 1


async def test_failed_transfer_endpoint_leaves_the_database_untouched(
    client: httpx.AsyncClient, bank: BankService
):
    source = await bank.open_account("alice", Decimal("10.00"))
    target = await bank.open_account("bob", Decimal("10.00"))

    response = await client.post(
        "/api/transfers",
        json={"source_id": source.id, "target_id": target.id, "amount": "99.00"},
    )

    assert response.status_code == 409
    assert (await client.get("/api/ledger")).json() == []
    assert (await client.get(f"/api/accounts/{source.id}")).json()["balance"] == "10.00"


async def test_unknown_account_returns_not_found(client: httpx.AsyncClient):
    response = await client.get("/api/accounts/4242")
    assert response.status_code == 404


async def test_a_duplicate_owner_is_a_conflict_not_a_crash(client: httpx.AsyncClient):
    """The unique index on owner is the check, so the refusal arrives as an
    IntegrityError out of the flush and has to reach the caller as a 409."""
    await client.post("/api/accounts", json={"owner": "alice", "initial_balance": "1.00"})

    response = await client.post(
        "/api/accounts", json={"owner": "alice", "initial_balance": "1.00"}
    )

    assert response.status_code == 409
    assert len((await client.get("/api/accounts")).json()) == 1


async def test_an_owner_longer_than_the_column_is_rejected(client: httpx.AsyncClient):
    response = await client.post(
        "/api/accounts", json={"owner": "x" * 200, "initial_balance": "1.00"}
    )

    assert response.status_code == 422


async def test_an_account_id_outside_the_column_range_is_rejected(
    client: httpx.AsyncClient,
):
    """id is an int4. A larger number is a malformed request, not a missing account,
    and it used to reach Postgres and come back as 'integer out of range'."""
    response = await client.get("/api/accounts/99999999999999")

    assert response.status_code == 422


async def test_a_sub_cent_amount_is_rejected(client: httpx.AsyncClient, bank: BankService):
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    response = await client.post(
        "/api/transfers",
        json={"source_id": source.id, "target_id": target.id, "amount": "0.005"},
    )

    assert response.status_code == 400
    assert (await client.get(f"/api/accounts/{target.id}")).json()["balance"] == "0.00"


async def test_an_amount_too_large_for_the_column_is_rejected(
    client: httpx.AsyncClient, bank: BankService
):
    account = await bank.open_account("alice", Decimal("100.00"))

    response = await client.post(
        f"/api/accounts/{account.id}/deposit", json={"amount": "1e30"}
    )

    assert response.status_code == 400
    assert (await client.get(f"/api/accounts/{account.id}")).json()["balance"] == "100.00"


async def test_a_request_that_cannot_get_a_connection_is_unavailable_not_a_crash(
    client: httpx.AsyncClient, bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    """lock_timeout bounds the wait for a row and arrives as an OperationalError. The
    wait for a connection out of the pool does not: SQLAlchemy raises its own
    TimeoutError, which is not an OperationalError, so it used to miss the 503 handler
    and leave the caller a 500 for a queue that was merely full."""
    account = await bank.open_account("alice", Decimal("100.00"))
    one_connection = create_async_engine(
        DATABASE_URL,
        pool_size=1,
        max_overflow=0,
        pool_timeout=1,
        connect_args={"options": TIMEOUTS},
    )
    monkeypatch.setattr(tx, "session_factory", async_sessionmaker(one_connection))
    holding = asyncio.Event()

    @transactional
    async def hold_the_only_connection() -> None:
        await bank.list_accounts()
        holding.set()
        await asyncio.sleep(5)

    hog = asyncio.create_task(hold_the_only_connection())
    await holding.wait()
    try:
        response = await client.get(f"/api/accounts/{account.id}")
        assert response.status_code == 503
    finally:
        hog.cancel()
        try:
            await hog
        except BaseException:
            pass
        await one_connection.dispose()


async def test_a_non_finite_amount_is_rejected_by_the_request_model(
    client: httpx.AsyncClient, bank: BankService
):
    """NaN and Infinity never reach the service: the request model refuses them, so
    they are a 422 and not the 400 every other bad amount gets. _check_money() still
    refuses them for a caller that reaches the service directly."""
    account = await bank.open_account("alice", Decimal("100.00"))

    for amount in ("NaN", "Infinity", "-Infinity"):
        response = await client.post(
            f"/api/accounts/{account.id}/deposit", json={"amount": amount}
        )
        assert response.status_code == 422, amount

    assert (await client.get(f"/api/accounts/{account.id}")).json()["balance"] == "100.00"


async def test_a_poisoned_transaction_reaching_the_controller_names_its_cause(
    client: httpx.AsyncClient, bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    """UnexpectedRollback means the service swallowed a failure it should not have,
    which is a bug and a 500. Without a handler it was an opaque 'Internal Server
    Error' that threw away the diagnosis the boundary worked to produce."""
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def swallowing_deposit(account_id: int, amount: Decimal):
        try:
            await bank.withdraw(account_id, Decimal("999.00"))
        except InsufficientFunds:
            pass
        return await bank.get_account(account_id)

    monkeypatch.setattr(controller.service, "deposit", swallowing_deposit)

    response = await client.post(
        f"/api/accounts/{account.id}/deposit", json={"amount": "1.00"}
    )

    assert response.status_code == 500
    assert response.json()["cause"].startswith("InsufficientFunds")
    assert (await client.get(f"/api/accounts/{account.id}")).json()["balance"] == "10.00"


async def test_the_how_it_works_page_shows_the_decorator_that_ships(
    client: httpx.AsyncClient,
):
    """The page annotates tx.py line by line, so a snippet that drifts from the source
    documents a boundary nobody is running. It once showed a recorder that caught
    DBAPIError and not CancelledError, which is a feature this README sells."""
    page = (await client.get("/")).text
    embedded = re.search(r"const TX_CODE = `(.*?)`;", page, re.S).group(1)
    source = Path(inspect.getsourcefile(tx)).read_text()

    assert source.rstrip("\n").endswith(embedded)
    assert embedded.startswith("def _running_task()")


async def test_a_taskgroup_inside_a_boundary_names_its_refusal(
    client: httpx.AsyncClient, bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    """A TaskGroup is the shape fan-out takes in modern async code, and it wraps what
    its children raise. CrossTaskTransaction arrives inside an ExceptionGroup, which is
    not an instance of it, so the handler that exists to name the diagnosis never
    matched and the caller got an opaque 'Internal Server Error' instead."""
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def grouped_deposit(account_id: int, amount: Decimal):
        async with asyncio.TaskGroup() as group:
            group.create_task(bank.list_accounts())

    monkeypatch.setattr(controller.service, "deposit", grouped_deposit)

    response = await client.post(
        f"/api/accounts/{account.id}/deposit", json={"amount": "1.00"}
    )

    assert response.status_code == 500
    assert "CrossTaskTransaction" in response.json()["cause"]
    assert (await client.get(f"/api/accounts/{account.id}")).json()["balance"] == "10.00"


async def test_a_blank_owner_is_refused_by_the_layer_that_can_see_it(
    client: httpx.AsyncClient,
):
    """min_length on the request model refuses the empty string, so that one is a 422.
    A string of spaces is a value the schema can hold and an account nobody can name, so
    it is the service that refuses it and a 400, the same way a sub-cent amount is."""
    assert (
        await client.post("/api/accounts", json={"owner": "", "initial_balance": "1.00"})
    ).status_code == 422

    response = await client.post(
        "/api/accounts", json={"owner": "   ", "initial_balance": "1.00"}
    )

    assert response.status_code == 400
    assert (await client.get("/api/accounts")).json() == []


async def test_the_readme_shows_the_decorator_that_ships():
    """The README prints the mechanism in full and calls it that, so a block that has
    drifted from the source documents a boundary nobody is running. The How it works
    page drifted exactly that way once, which is why both are pinned now."""
    source = Path(inspect.getsourcefile(tx))
    readme = (source.parent.parent / "README.md").read_text()
    blocks = re.findall(r"```python\n(.*?)```", readme, re.S)

    assert len(blocks) == 2
    for block in blocks:
        assert block in source.read_text(), block.splitlines()[0]


async def test_the_readme_lists_the_tests_that_run():
    """The README sells a number and prints the names, and both had drifted: it claimed
    96 while the suite ran 104, and the list was missing nine of them. A count nobody
    checks is the same drift the pinned code blocks exist to stop, one file over. The
    names come from the files rather than from what this run collected, so the check
    means the same thing under -k as it does under a full run."""
    root = Path(inspect.getsourcefile(tx)).parent.parent
    readme = (root / "README.md").read_text()
    defined = sorted(
        f"tests/{path.name}::{name}"
        for path in (root / "tests").glob("test_*.py")
        for name in re.findall(r"^async def (test_\w+)", path.read_text(), re.M)
    )
    listed = sorted(re.findall(r"^(tests/\S+::\S+) PASSED$", readme, re.M))

    assert listed == defined
    assert f"\n{len(defined)} passed" in readme
    assert f"# {len(defined)} tests against a real postgres" in readme


async def test_an_amount_past_the_decimal_contexts_limit_is_a_bad_request(
    client: httpx.AsyncClient,
):
    """The request model parses any finite Decimal, so an exponent above the decimal
    context's Emax reached the service and abs() raised decimal.Overflow there. Nothing
    handles an ArithmeticError, so an amount too large for the column left as an opaque
    500 on every route that takes money, which is the one answer the API promises it is
    not."""
    source = (
        await client.post(
            "/api/accounts", json={"owner": "alice", "initial_balance": "100.00"}
        )
    ).json()
    target = (
        await client.post(
            "/api/accounts", json={"owner": "bob", "initial_balance": "100.00"}
        )
    ).json()
    past_emax = "1E+999999999"

    calls = [
        ("/api/accounts", {"owner": "carol", "initial_balance": past_emax}),
        (f"/api/accounts/{source['id']}/deposit", {"amount": past_emax}),
        (f"/api/accounts/{source['id']}/withdraw", {"amount": past_emax}),
        (
            "/api/transfers",
            {"source_id": source["id"], "target_id": target["id"], "amount": past_emax},
        ),
    ]
    for path, body in calls:
        response = await client.post(path, json=body)
        assert response.status_code == 400, path
        assert response.json()["error"] == "amount is too large to store"

    assert (await client.get(f"/api/accounts/{source['id']}")).json()["balance"] == "100.00"


async def test_every_connection_carries_the_timeouts_the_app_configures(
    bank: BankService,
):
    """The two timeouts arrive as libpq options on the connection string, which is the
    kind of setting that is either applied to every connection or silently to none. The
    tests below shorten them to run in milliseconds instead of seconds, so this is what
    says the shipped numbers are really on the socket."""

    @transactional
    async def ask_postgres() -> tuple[str, str]:
        session = current_session()
        lock = await session.execute(text("show lock_timeout"))
        statement = await session.execute(text("show statement_timeout"))
        return lock.scalar_one(), statement.scalar_one()

    assert await ask_postgres() == ("5s", "15s")


async def test_a_wait_longer_than_lock_timeout_is_unavailable_not_a_crash(
    client: httpx.AsyncClient, bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    """The pool timeout above has a test because it needed a handler of its own. The
    lock timeout is the one the README leads with, and it had none: a hot account held
    by a stalled transaction is the case lock_timeout exists for, and the caller has to
    see a 503 rather than a hang or the OperationalError as an opaque 500. The wait is
    shortened to a fifth of a second here so the suite does not spend the shipped five
    on it; the test above is what pins the shipped number."""
    account = await bank.open_account("alice", Decimal("100.00"))
    impatient = create_async_engine(
        DATABASE_URL, connect_args={"options": "-c lock_timeout=200"}
    )
    monkeypatch.setattr(tx, "session_factory", async_sessionmaker(impatient))
    holding, release = asyncio.Event(), asyncio.Event()

    @transactional
    async def hold_the_row() -> None:
        await AccountDAO().find_for_update(account.id)
        holding.set()
        await release.wait()

    holder = asyncio.create_task(hold_the_row())
    await holding.wait()
    try:
        response = await client.post(
            f"/api/accounts/{account.id}/deposit", json={"amount": "1.00"}
        )
    finally:
        release.set()
        await holder
        await impatient.dispose()

    assert response.status_code == 503, response.text


async def test_a_statement_past_its_timeout_is_unavailable_not_a_crash(
    client: httpx.AsyncClient, bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    """The third of the three bounded waits. statement_timeout kills a query Postgres is
    still running, which arrives as an OperationalError like the lock timeout does, and
    the README promises all three answer 503 rather than leaving the request hanging.
    SET LOCAL shortens it inside the boundary so the wait is milliseconds rather than
    the shipped fifteen seconds."""

    @transactional
    async def sleep_past_the_timeout(account_id: int, amount: Decimal):
        session = current_session()
        await session.execute(text("set local statement_timeout = 200"))
        await session.execute(text("select pg_sleep(5)"))

    monkeypatch.setattr(controller.service, "deposit", sleep_past_the_timeout)

    response = await client.post("/api/accounts/1/deposit", json={"amount": "1.00"})

    assert response.status_code == 503, response.text


async def test_an_amount_that_is_not_a_positive_number_is_a_bad_request(
    client: httpx.AsyncClient, bank: BankService
):
    """Zero and a negative amount are values the schema holds happily, so the request
    model has no reason to refuse them and the service is the layer that can. A negative
    deposit is a withdrawal with no funds check behind it, which is the one that would
    matter."""
    account = await bank.open_account("alice", Decimal("100.00"))

    for path in ("deposit", "withdraw"):
        for amount in ("0.00", "-1.00"):
            response = await client.post(
                f"/api/accounts/{account.id}/{path}", json={"amount": amount}
            )
            assert response.status_code == 400, (path, amount, response.text)

    assert (await client.get(f"/api/accounts/{account.id}")).json()["balance"] == "100.00"


async def test_a_value_the_schema_cannot_hold_is_a_bad_request_not_a_crash(
    client: httpx.AsyncClient, bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    """The DataError handler is there for the bug that gets past the service, and a
    handler nothing exercises is a handler nobody knows is wired up. A service that
    stopped checking the column's range is exactly that bug, and the answer has to stay
    a 400 naming the range rather than an opaque 500."""
    account = await bank.open_account("alice", Decimal("100.00"))
    monkeypatch.setattr(service_module, "MAX_MONEY", Decimal("1E+30"))

    response = await client.post(
        f"/api/accounts/{account.id}/deposit", json={"amount": "1E+20"}
    )

    assert response.status_code == 400
    assert "out of range" in response.json()["error"]
    assert (await client.get(f"/api/accounts/{account.id}")).json()["balance"] == "100.00"


async def test_the_ui_only_calls_routes_the_api_really_has(client: httpx.AsyncClient):
    """The page is served by the same app it calls, so a route renamed on one side and
    not the other is a 404 nobody sees until they click. Every path the page builds is
    checked against the routing table rather than against the README."""
    page = (await client.get("/")).text
    paths = set(re.findall(r"call\('(\w+)', '(/api/[^']*)'", page))
    operations = set(re.findall(r'<button class="go" value="(\w+)"', page))
    paths |= {("POST", f"/api/accounts/{{}}/{operation}") for operation in operations}
    known = {
        (method, re.sub(r"\{[^}]+\}", "{}", route.path))
        for route in app.routes
        for method in getattr(route, "methods", ())
    }

    assert operations
    assert {(method, path.rstrip("/")) for method, path in paths} <= known


async def test_the_readme_documents_every_route_the_api_has():
    """The API table is the contract a reader works from, so a route added without a row
    is undocumented and a row without a route is a lie. Both directions are checked,
    because the drift that already happened here went the way nobody looks."""
    source = Path(inspect.getsourcefile(tx))
    readme = (source.parent.parent / "README.md").read_text()
    documented = {
        (method, path)
        for method, path in re.findall(r"^\| `(\w+)` \| `(/[^`]*)`", readme, re.M)
    }
    served = {
        (method, re.sub(r"\{[^}]+\}", "{id}", route.path))
        for route in app.routes
        for method in getattr(route, "methods", ())
        if route.path.startswith("/api") or route.path == "/"
    } - {("HEAD", "/"), ("HEAD", "/api/accounts")}

    assert documented == served


async def test_the_ui_code_blocks_show_the_service_and_dao_that_ship(
    client: httpx.AsyncClient,
):
    """The decorator on the page is pinned to tx.py, and the other two cards were not.
    They quote transfer(), find_all_for_update() and the constraints that make the lock
    order work, which is the same drift risk one file over: a page annotating a lock
    order nobody takes reads exactly like a page annotating one somebody does. The
    signature is reflowed to fit the card, so the comparison ignores whitespace and
    every other token has to be a token that ships."""
    page = (await client.get("/")).text
    root = Path(inspect.getsourcefile(tx)).parent
    models = (root / "models.py").read_text()
    blocks = {
        "SERVICE_CODE": root / "service.py",
        "LOCK_CODE": root / "dao.py",
    }

    for name, path in blocks.items():
        quoted = re.search(rf"const {name} = `(.*?)`;", page, re.S).group(1)
        sources = "".join((path.read_text() + models).split())
        for line in quoted.splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            assert "".join(line.split()) in sources, (name, line.strip())


async def test_the_ui_only_touches_elements_the_page_declares(
    client: httpx.AsyncClient,
):
    """The page is one file, so its script and its markup drift together or not at all,
    and a renamed id is a button that silently stops working rather than an error
    anybody sees. Every element the script reaches for has to be one the page declares,
    and every code block it fills has to have somewhere to go."""
    page = (await client.get("/")).text
    declared = set(re.findall(r'\bid="([^"]+)"', page))
    reached = set(re.findall(r"getElementById\('([^']+)'\)", page))
    filled = set(re.findall(r"renderCode\('([^']+)'", page))

    assert reached
    assert filled
    assert (reached | filled) <= declared
