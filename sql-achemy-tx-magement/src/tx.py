from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from functools import wraps
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from db import session_factory

_current_session: ContextVar[AsyncSession | None] = ContextVar(
    "current_session", default=None
)


class NoActiveTransaction(RuntimeError):
    pass


def current_session() -> AsyncSession:
    session = _current_session.get()
    if session is None:
        raise NoActiveTransaction("no active transaction, caller is not @transactional")
    return session


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
