from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from db import session_factory


@dataclass
class TransactionContext:
    session: AsyncSession
    rollback_only: bool = False


_current: ContextVar[TransactionContext | None] = ContextVar("current", default=None)


class NoActiveTransaction(RuntimeError):
    pass


class UnexpectedRollback(RuntimeError):
    pass


def current_session() -> AsyncSession:
    context = _current.get()
    if context is None:
        raise NoActiveTransaction("no active transaction, caller is not @transactional")
    return context.session


def transactional[T](func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        joined = _current.get()
        if joined is not None:
            try:
                return await func(*args, **kwargs)
            except Exception:
                joined.rollback_only = True
                raise
        async with session_factory() as session:
            context = TransactionContext(session)
            token = _current.set(context)
            try:
                async with session.begin():
                    result = await func(*args, **kwargs)
                    if context.rollback_only:
                        raise UnexpectedRollback(
                            "a joined call failed and marked the transaction rollback-only"
                        )
                    return result
            finally:
                _current.reset(token)

    return wrapper
