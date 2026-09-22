from sqlalchemy import select

from library.db import make_engine, session_scope
from library.models import Book
from library.repository import add_book, books_by_author, list_books
from library.schemas import BookIn

SEED: list[BookIn] = [
    BookIn(title="Dune", year=1965, author="Frank Herbert", isbn="978-0441172719"),
    BookIn(title="Children of Dune", year=1976, author="Frank Herbert"),
    BookIn(title="Neuromancer", year=1984, author="William Gibson", isbn="978-0441569595"),
]


def seed() -> None:
    with session_scope(make_engine()) as session:
        if session.scalar(select(Book.id).limit(1)) is None:
            for data in SEED:
                add_book(session, data)


def report() -> None:
    with session_scope(make_engine()) as session:
        print("All books:")
        for book in list_books(session):
            print(book.model_dump_json())
        print("Books by Frank Herbert:")
        for book in books_by_author(session, "Frank Herbert"):
            print(f"{book.year} {book.title}")


def main() -> None:
    seed()
    report()


if __name__ == "__main__":
    main()
