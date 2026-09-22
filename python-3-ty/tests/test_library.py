import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from library.db import make_engine
from library.repository import add_book, books_by_author, list_books
from library.schemas import BookIn
from tests.conftest import ROOT


def test_migration_creates_schema_matching_models(db_url: str) -> None:
    tables = set(inspect(make_engine(db_url)).get_table_names())
    assert {"authors", "books", "alembic_version"} <= tables


def test_migration_downgrade_removes_tables(db_url: str) -> None:
    command.downgrade(Config(str(ROOT / "alembic.ini")), "base")
    tables = set(inspect(make_engine(db_url)).get_table_names())
    assert "books" not in tables and "authors" not in tables


def test_same_author_is_reused_across_books(session: Session) -> None:
    first = add_book(session, BookIn(title="Dune", year=1965, author="Frank Herbert"))
    second = add_book(session, BookIn(title="Dune Messiah", year=1969, author="Frank Herbert"))
    assert first.author_name == second.author_name
    assert [b.title for b in books_by_author(session, "Frank Herbert")] == ["Dune", "Dune Messiah"]


def test_books_are_listed_oldest_first(session: Session) -> None:
    add_book(session, BookIn(title="Neuromancer", year=1984, author="William Gibson"))
    add_book(session, BookIn(title="Dune", year=1965, author="Frank Herbert"))
    assert [b.year for b in list_books(session)] == [1965, 1984]


def test_duplicate_isbn_is_rejected_by_database(session: Session) -> None:
    add_book(session, BookIn(title="A", year=2000, author="X", isbn="978-0000000001"))
    with pytest.raises(IntegrityError):
        add_book(session, BookIn(title="B", year=2001, author="Y", isbn="978-0000000001"))


@pytest.mark.parametrize(
    "fields",
    [
        {"title": "", "year": 2000, "author": "X"},
        {"title": "T", "year": 1000, "author": "X"},
        {"title": "T", "year": 2000, "author": "X", "isbn": "not-an-isbn"},
    ],
)
def test_invalid_input_never_reaches_database(fields: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        BookIn.model_validate(fields)
