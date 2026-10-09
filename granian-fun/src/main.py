import json
from typing import Protocol
from urllib.parse import parse_qsl

from api import TaskApi
from tasks import TaskStore
from web import Request

JSON_HEADERS: list[tuple[str, str]] = [("content-type", "application/json")]


class Scope(Protocol):
    @property
    def method(self) -> str: ...

    @property
    def path(self) -> str: ...

    @property
    def query_string(self) -> str: ...


class Transport(Protocol):
    async def __call__(self) -> bytes: ...

    def response_empty(self, status: int, headers: list[tuple[str, str]]) -> None: ...

    def response_str(self, status: int, headers: list[tuple[str, str]], body: str) -> None: ...


router = TaskApi(TaskStore()).router()


async def app(scope: Scope, transport: Transport) -> None:
    query = dict(parse_qsl(scope.query_string))
    response = router.dispatch(Request(scope.method, scope.path, query, await transport()))
    if response.status == 204:
        transport.response_empty(response.status, [])
    else:
        transport.response_str(response.status, JSON_HEADERS, json.dumps(response.payload))
