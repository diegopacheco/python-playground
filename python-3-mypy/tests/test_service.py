import pytest
from pydantic import ValidationError
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from library import service
from library.db import make_engine
from library.models import Author
from library.schemas import BookIn


def test_migrations_create_every_table(migrated: str) -> None:
    tables = set(inspect(make_engine(migrated)).get_table_names())
    assert {"authors", "books", "alembic_version"} <= tables


def test_books_by_same_author_share_one_author_row(session: Session) -> None:
    first = service.add_book(session, BookIn(title="A", pages=10, price=1.0, author="X"))
    second = service.add_book(session, BookIn(title="B", pages=20, price=2.0, author="X"))
    assert first.author_id == second.author_id
    assert session.query(Author).count() == 1


def test_stats_reflect_persisted_books(session: Session) -> None:
    service.add_book(session, BookIn(title="Cheap", pages=100, price=10.0, author="X"))
    service.add_book(session, BookIn(title="Pricey", pages=300, price=30.0, author="Y"))
    result = service.library_stats(session)
    assert result.books == 2
    assert result.total_pages == 400
    assert result.average_price == 20.0
    assert result.most_expensive == "Pricey"


def test_invalid_book_never_reaches_database() -> None:
    with pytest.raises(ValidationError):
        BookIn(title="", pages=0, price=-1.0, author="X")


def test_author_name_is_unique_in_schema(session: Session) -> None:
    session.add(Author(name="Dup"))
    session.commit()
    session.add(Author(name="Dup"))
    with pytest.raises(IntegrityError):
        session.commit()
