import asyncio
import inspect
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from db import session_factory

ROLLBACK_ONLY = "a failure inside the boundary marked the transaction rollback-only"
LOST_TRANSACTION = "the transaction was closed or deactivated inside the boundary"
UNGUARDABLE = frozenset({"stream", "stream_scalars"})
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
        "get_transaction",
        "sync_session",
        "run_sync",
        "_proxied",
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


class BoundarySession:
    def __init__(self, session: AsyncSession, context: "TransactionContext") -> None:
        self._session = session
        self._context = context

    def __getattr__(self, name: str) -> Any:
        if self._context.closed:
            raise NoActiveTransaction(
                "the transaction this session belonged to has already ended"
            )
        _check_task(self._context)
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
        attribute = getattr(self._session, name)
        if not inspect.iscoroutinefunction(attribute):
            return attribute

        @wraps(attribute)
        async def guarded(*args: Any, **kwargs: Any) -> Any:
            try:
                return await attribute(*args, **kwargs)
            except (DBAPIError, asyncio.CancelledError) as error:
                if self._context.failure is None:
                    self._context.failure = error
                raise

        return guarded


@dataclass
class TransactionContext:
    task: asyncio.Task[Any] | None
    failure: BaseException | None = None
    closed: bool = False
    session: BoundarySession = field(init=False)


_current: ContextVar[TransactionContext | None] = ContextVar("current", default=None)


def _active() -> TransactionContext | None:
    context = _current.get()
    if context is not None:
        _check_task(context)
    return context


def current_session() -> BoundarySession:
    context = _active()
    if context is None:
        raise NoActiveTransaction("no active transaction, caller is not @transactional")
    return context.session


def transactional[T](func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    if not inspect.iscoroutinefunction(func):
        raise TypeError(f"@transactional needs an async def, {func.__name__} is not one")

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
                        if context.failure is not None and error is not context.failure:
                            raise UnexpectedRollback(ROLLBACK_ONLY) from context.failure
                        raise
                    if context.failure is not None:
                        raise UnexpectedRollback(ROLLBACK_ONLY) from context.failure
                    transaction = session.get_transaction()
                    if transaction is None or not transaction.is_active:
                        raise UnexpectedRollback(LOST_TRANSACTION)
                    return result
            finally:
                context.closed = True
                _current.reset(token)

    return wrapper
