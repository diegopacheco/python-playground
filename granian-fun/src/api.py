from dataclasses import asdict

from tasks import Draft, Task, TaskStore
from web import HttpError, Json, Request, Response, Router, route

DONE_FILTERS: dict[str, bool] = {"true": True, "false": False}


def to_json(task: Task) -> Json:
    return asdict(task)


def parse_draft(payload: Json) -> Draft:
    match payload:
        case {"title": str(title), "done": bool(done)} if title.strip():
            return Draft(title.strip(), done)
        case {"title": str(title), **rest} if title.strip() and "done" not in rest:
            return Draft(title.strip())
    raise HttpError(400, "body must have a non-empty string title and an optional boolean done")


def parse_done(request: Request) -> bool | None:
    raw = request.query.get("done")
    if raw is None:
        return None
    if raw not in DONE_FILTERS:
        raise HttpError(400, "done must be true or false")
    return DONE_FILTERS[raw]


def parse_id(request: Request) -> int:
    raw = request.params["id"]
    if not raw.isdecimal():
        raise HttpError(404, f"task {raw} was not found")
    return int(raw)


def found(task: Task | None, task_id: int) -> Task:
    if task is None:
        raise HttpError(404, f"task {task_id} was not found")
    return task


class TaskApi:
    def __init__(self, store: TaskStore) -> None:
        self.store = store

    def router(self) -> Router:
        return Router(
            [
                route("GET", "/health", self.health),
                route("GET", "/tasks", self.list),
                route("POST", "/tasks", self.create),
                route("GET", "/tasks/{id}", self.read),
                route("PUT", "/tasks/{id}", self.update),
                route("DELETE", "/tasks/{id}", self.delete),
            ]
        )

    def health(self, request: Request) -> Response:
        return Response(200, {"status": "up", "tasks": len(self.store.all())})

    def list(self, request: Request) -> Response:
        return Response(200, [to_json(task) for task in self.store.all(parse_done(request))])

    def create(self, request: Request) -> Response:
        return Response(201, to_json(self.store.add(parse_draft(request.json()))))

    def read(self, request: Request) -> Response:
        task_id = parse_id(request)
        return Response(200, to_json(found(self.store.get(task_id), task_id)))

    def update(self, request: Request) -> Response:
        task_id = parse_id(request)
        draft = parse_draft(request.json())
        return Response(200, to_json(found(self.store.replace(task_id, draft), task_id)))

    def delete(self, request: Request) -> Response:
        task_id = parse_id(request)
        if not self.store.remove(task_id):
            raise HttpError(404, f"task {task_id} was not found")
        return Response(204)
