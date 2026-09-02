import json
import os
from pathlib import Path

DATA = Path(
    os.environ.get("QRPOC_DATA", Path(__file__).resolve().parent.parent / "data")
)
ORIGINALS = DATA / "originals"
PAGES = DATA / "pages"
CAPTURES = DATA / "captures"
INDEX = DATA / "index.json"

for folder in (ORIGINALS, PAGES, CAPTURES):
    folder.mkdir(parents=True, exist_ok=True)


def _read() -> dict:
    if not INDEX.exists():
        return {}
    return json.loads(INDEX.read_text())


def _write(index: dict) -> None:
    INDEX.write_text(json.dumps(index, indent=2))


def record(page_id: str, entry: dict) -> None:
    index = _read()
    index.setdefault(page_id, {}).update(entry)
    _write(index)


def get(page_id: str) -> dict | None:
    return _read().get(page_id)


def all_pairs() -> dict:
    return _read()
