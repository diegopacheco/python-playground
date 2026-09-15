import uuid
from typing import Awaitable, Callable

import aiosqlite
from fastapi import Request, Response

from dao import GameDao
from service import GameService

CallNext = Callable[[Request], Awaitable[Response]]


def request_state(db_path: str) -> Callable[[Request, CallNext], Awaitable[Response]]:
    async def middleware(request: Request, call_next: CallNext) -> Response:
        request.state.request_id = str(uuid.uuid4())
        async with aiosqlite.connect(db_path) as conn:
            request.state.game_service = GameService(GameDao(conn))
            response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    return middleware
