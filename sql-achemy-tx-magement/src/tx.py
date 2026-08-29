import asyncio
import inspect
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from itertools import count
from typing import Any, NoReturn

from psycopg.pq import TransactionStatus
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, AsyncTransaction
from sqlalchemy.orm import Session
from sqlalchemy.util import greenlet_spawn

from db import session_factory

ROLLBACK_ONLY = "a failure inside the boundary marked the transaction rollback-only"
LOST_TRANSACTION = "the transaction was closed or deactivated inside the boundary"
LOST_CONNECTION = "the transaction was ended on the connection under the boundary"
SPLIT_CONNECTION = (
    "the transaction under the boundary was ended and another one opened in its place"
)
DISCARDED_BY_POSTGRES = (
    "postgres is no longer in the transaction the boundary opened, so it has already "
    "committed it, rolled it back or aborted it"
)
LOST_MARK = (
    "the mark the boundary set on its transaction is gone, so that transaction ended "
    "and postgres is in another one"
)
MARK = "application_name"
NOT_YOURS_TO_CLOSE = (
    "the session's own context manager closes it on exit; @transactional opened this "
    "transaction and is the only thing that ends it"
)
NOT_YOURS_TO_HOLD = (
    "a context manager the session hands out yields the sync Session and carries it in "
    "the frame too; entering and exiting cross the boundary and nothing else does"
)
UNGUARDABLE = frozenset({"stream", "stream_scalars"})
THE_WRAPPERS_OWN = frozenset({"_session", "_context"})
OWNED_BY_THE_BOUNDARY = frozenset(
    {
        "commit",
        "rollback",
        "close",
        "aclose",
        "close_all",
        "reset",
        "invalidate",
        "begin",
        "begin_nested",
        "connection",
        "get_bind",
        "bind",
        "get_transaction",
        "get_nested_transaction",
        "identity_map",
        "sync_session",
        "object_session",
        "run_sync",
        "_proxied",
        "_proxy_objects",
        "_maker_context_manager",
    }
)


class NoActiveTransaction(RuntimeError):
    pass


class CrossTaskTransaction(RuntimeError):
    pass


class UnexpectedRollback(RuntimeError):
    pass


class TransactionNotYours(RuntimeError):
    pass


def _running_task() -> asyncio.Task[Any] | None:
    try:
        return asyncio.current_task()
    except RuntimeError:
        return None


def _check_task(context: "TransactionContext") -> None:
    if context.task is not _running_task():
        raise CrossTaskTransaction(
            "the transaction belongs to the task that opened it, an AsyncSession "
            "cannot be driven from anywhere else"
        )


def _driver_of(connection: Any) -> Any:
    return connection.sync_connection.connection.dbapi_connection


def _in_transaction(driver: Any) -> bool:
    return driver.info.transaction_status == TransactionStatus.INTRANS


def _mark_of(driver: Any) -> str:
    return driver.info.parameter_status(MARK)


def _is_context_manager(value: Any) -> bool:
    kind = type(value)
    return hasattr(kind, "__enter__") and hasattr(kind, "__exit__")


class BoundaryContext:
    def __init__(self, manager: Any, boundary: "BoundarySession") -> None:
        self.__manager = manager
        self.__boundary = boundary

    def __enter__(self) -> Any:
        self.__boundary._guard()
        entered = self.__manager.__enter__()
        if isinstance(entered, (Session, AsyncSession)):
            return self.__boundary
        return entered

    def __exit__(self, *unused: Any) -> Any:
        return self.__manager.__exit__(*unused)

    def __getattr__(self, name: str) -> Any:
        raise TransactionNotYours(f"{name} is not yours to reach, {NOT_YOURS_TO_HOLD}")


class BoundarySession:
    def __init__(self, session: AsyncSession, context: "TransactionContext") -> None:
        self._session = session
        self._context = context

    def _guard(self) -> None:
        if self._context.closed:
            raise NoActiveTransaction(
                "the transaction this session belonged to has already ended"
            )
        _check_task(self._context)

    def _refuse(self, name: str) -> None:
        if name in OWNED_BY_THE_BOUNDARY:
            raise TransactionNotYours(
                f"{name} belongs to @transactional, not to the code inside it"
            )
        if name in UNGUARDABLE:
            raise TransactionNotYours(
                f"{name}() raises from the cursor while the result is iterated, where "
                "the boundary cannot see it; use execute() so a failure poisons the "
                "transaction instead of being committed over"
            )

    async def _open(self) -> None:
        context = self._context
        if context.driver is not None:
            return
        connection = await self._session.connection()
        mark = f"boundary-{next(_boundaries)}"
        await connection.exec_driver_sql(f"set local {MARK} = '{mark}'")
        context.transaction = connection.get_transaction()
        context.driver = _driver_of(connection)
        context.mark = mark

    async def __aenter__(self) -> "BoundarySession":
        raise TransactionNotYours(NOT_YOURS_TO_CLOSE)

    async def __aexit__(self, *unused: Any) -> None:
        raise TransactionNotYours(NOT_YOURS_TO_CLOSE)

    def __contains__(self, instance: Any) -> bool:
        self._guard()
        return instance in self._session

    def __iter__(self) -> Any:
        self._guard()
        return iter(self._session)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in THE_WRAPPERS_OWN:
            object.__setattr__(self, name, value)
            return
        self._guard()
        self._refuse(name)
        setattr(self._session, name, value)

    def __delattr__(self, name: str) -> None:
        self._guard()
        self._refuse(name)
        delattr(self._session, name)

    def __getattr__(self, name: str) -> Any:
        self._guard()
        self._refuse(name)
        attribute = getattr(self._session, name)
        if not inspect.isroutine(attribute):
            if _is_context_manager(attribute):
                return BoundaryContext(attribute, self)
            return attribute
        if not inspect.iscoroutinefunction(attribute):

            @wraps(attribute)
            def checked(*args: Any, **kwargs: Any) -> Any:
                self._guard()
                return attribute(*args, **kwargs)

            return checked

        @wraps(attribute)
        async def guarded(*args: Any, **kwargs: Any) -> Any:
            self._guard()
            try:
                await self._open()
                answer = await attribute(*args, **kwargs)
            except (DBAPIError, asyncio.CancelledError) as error:
                if self._context.failure is None:
                    self._context.failure = error
                raise
            return answer

        return guarded


@dataclass
class TransactionContext:
    task: asyncio.Task[Any] | None
    failure: BaseException | None = None
    closed: bool = False
    transaction: AsyncTransaction | None = None
    driver: Any = None
    mark: str = ""
    session: BoundarySession = field(init=False)


_boundaries = count()
_current: ContextVar[TransactionContext | None] = ContextVar("current", default=None)


def _active() -> TransactionContext | None:
    context = _current.get()
    if context is None or context.closed:
        return None
    _check_task(context)
    return context


def current_session() -> BoundarySession:
    context = _active()
    if context is None:
        raise NoActiveTransaction("no active transaction, caller is not @transactional")
    return context.session


async def _leave_no_transaction_open(context: "TransactionContext") -> None:
    driver = context.driver
    if driver is None or not _in_transaction(driver):
        return
    if _mark_of(driver) == context.mark:
        await greenlet_spawn(driver.rollback)


def _rollback_only(failure: BaseException) -> NoReturn:
    task = _running_task()
    cancelled = isinstance(failure, asyncio.CancelledError)
    if cancelled and task is not None and task.cancelling():
        raise failure
    raise UnexpectedRollback(ROLLBACK_ONLY) from failure


def transactional[T](func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    if not inspect.iscoroutinefunction(func):
        name = getattr(func, "__name__", type(func).__name__)
        raise TypeError(f"@transactional needs an async def, {name} is not one")

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
            context = TransactionContext(asyncio.current_task())
            context.session = BoundarySession(session, context)
            token = _current.set(context)
            try:
                async with session.begin():
                    try:
                        result = await func(*args, **kwargs)
                    except BaseException as error:
                        if context.failure is None or error is context.failure:
                            raise
                        if not isinstance(error, Exception):
                            raise error from context.failure
                        _rollback_only(context.failure)
                    if context.failure is not None:
                        _rollback_only(context.failure)
                    transaction = session.get_transaction()
                    if transaction is None or not transaction.is_active:
                        raise UnexpectedRollback(LOST_TRANSACTION)
                    if context.driver is not None:
                        connection = await session.connection()
                        if not connection.in_transaction():
                            raise UnexpectedRollback(LOST_CONNECTION)
                        if connection.get_transaction() is not context.transaction:
                            raise UnexpectedRollback(SPLIT_CONNECTION)
                        driver = _driver_of(connection)
                        if driver is not context.driver or not _in_transaction(driver):
                            raise UnexpectedRollback(DISCARDED_BY_POSTGRES)
                        if _mark_of(driver) != context.mark:
                            raise UnexpectedRollback(LOST_MARK)
                    return result
            finally:
                context.closed = True
                _current.reset(token)
                await _leave_no_transaction_open(context)

    return wrapper
