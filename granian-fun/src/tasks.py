from dataclasses import dataclass
from itertools import count


@dataclass(frozen=True, slots=True)
class Draft:
    title: str
    done: bool = False


@dataclass(frozen=True, slots=True)
class Task:
    id: int
    title: str
    done: bool


class TaskStore:
    def __init__(self) -> None:
        self.tasks: dict[int, Task] = {}
        self.ids = count(1)

    def all(self, done: bool | None = None) -> list[Task]:
        return [task for task in self.tasks.values() if done is None or task.done == done]

    def get(self, task_id: int) -> Task | None:
        return self.tasks.get(task_id)

    def add(self, draft: Draft) -> Task:
        return self.save(next(self.ids), draft)

    def replace(self, task_id: int, draft: Draft) -> Task | None:
        if task_id not in self.tasks:
            return None
        return self.save(task_id, draft)

    def remove(self, task_id: int) -> bool:
        return self.tasks.pop(task_id, None) is not None

    def save(self, task_id: int, draft: Draft) -> Task:
        task = Task(task_id, draft.title, draft.done)
        self.tasks[task_id] = task
        return task
