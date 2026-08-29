import asyncio
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from db import session_factory

ROLLBACK_ONLY = "a joined call failed and marked the transaction rollback-only"


@dataclass
class TransactionContext:
    session: AsyncSession
    task: asyncio.Task[Any] | None
    failure: BaseException | None = None


_current: ContextVar[TransactionContext | None] = ContextVar("current", default=None)


class NoActiveTransaction(RuntimeError):
    pass


class CrossTaskTransaction(RuntimeError):
    pass


class UnexpectedRollback(RuntimeError):
    pass


def _active() -> TransactionContext | None:
    context = _current.get()
    if context is not None and context.task is not asyncio.current_task():
        raise CrossTaskTransaction(
            "the transaction belongs to another task, an AsyncSession cannot be shared"
        )
    return context


def current_session() -> AsyncSession:
    context = _active()
    if context is None:
        raise NoActiveTransaction("no active transaction, caller is not @transactional")
    return context.session


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
