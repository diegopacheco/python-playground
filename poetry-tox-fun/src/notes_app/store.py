from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock

MAX_TITLE = 120
MAX_BODY = 2000


class NoteError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Note:
    id: int
    title: str
    body: str
    created_at: str


def clean_text(value: object, field: str, limit: int, required: bool) -> str:
    if not isinstance(value, str):
        raise NoteError(f"{field} must be a string")
    text = value.strip()
    if required and not text:
        raise NoteError(f"{field} is required")
    if len(text) > limit:
        raise NoteError(f"{field} must have at most {limit} characters")
    return text


class NoteStore:
    def __init__(self) -> None:
        self._notes: dict[int, Note] = {}
        self._next_id = 1
        self._lock = Lock()

    def all(self) -> list[Note]:
        with self._lock:
            return sorted(self._notes.values(), key=lambda note: note.id, reverse=True)

    def get(self, note_id: int) -> Note | None:
        with self._lock:
            return self._notes.get(note_id)

    def add(self, title: object, body: object) -> Note:
        clean_title = clean_text(title, "title", MAX_TITLE, required=True)
        clean_body = clean_text(body, "body", MAX_BODY, required=False)
        with self._lock:
            note = Note(self._next_id, clean_title, clean_body, datetime.now(UTC).isoformat(timespec="seconds"))
            self._notes[note.id] = note
            self._next_id += 1
            return note

    def delete(self, note_id: int) -> bool:
        with self._lock:
            return self._notes.pop(note_id, None) is not None
