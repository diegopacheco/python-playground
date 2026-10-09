import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace

type Json = None | bool | int | float | str | list[Json] | dict[str, Json]
type Handler = Callable[[Request], Response]


class HttpError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass(frozen=True, slots=True)
class Request:
    method: str
    path: str
    query: dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    params: dict[str, str] = field(default_factory=dict)

    def json(self) -> Json:
        try:
            payload: Json = json.loads(self.body)
        except ValueError:
            raise HttpError(400, "body is not valid JSON") from None
        return payload


@dataclass(frozen=True, slots=True)
class Response:
    status: int
    payload: Json = None


@dataclass(frozen=True, slots=True)
class Route:
    method: str
    pattern: re.Pattern[str]
    handler: Handler


def route(method: str, path: str, handler: Handler) -> Route:
    pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path)
    return Route(method, re.compile(pattern), handler)


class Router:
    def __init__(self, routes: list[Route]) -> None:
        self.routes = routes

    def dispatch(self, request: Request) -> Response:
        try:
            return self.resolve(request)
        except HttpError as error:
            return Response(error.status, {"error": error.message})

    def resolve(self, request: Request) -> Response:
        path_known = False
        for candidate in self.routes:
            found = candidate.pattern.fullmatch(request.path)
            if found is None:
                continue
            if candidate.method == request.method:
                return candidate.handler(replace(request, params=found.groupdict()))
            path_known = True
        if path_known:
            raise HttpError(405, f"{request.method} is not allowed on {request.path}")
        raise HttpError(404, f"{request.path} was not found")
