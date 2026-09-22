from sqlalchemy import select
from sqlalchemy.orm import Session

from library.models import Author, Book
from library.schemas import BookIn, BookOut


def to_out(book: Book) -> BookOut:
    return BookOut(
        id=book.id,
        title=book.title,
        year=book.year,
        isbn=book.isbn,
        author_name=book.author.name,
    )


def get_or_create_author(session: Session, name: str) -> Author:
    author = session.scalar(select(Author).where(Author.name == name))
    if author is None:
        author = Author(name=name)
        session.add(author)
        session.flush()
    return author


def add_book(session: Session, data: BookIn) -> BookOut:
    author = get_or_create_author(session, data.author)
    book = Book(title=data.title, year=data.year, isbn=data.isbn, author=author)
    session.add(book)
    session.flush()
    return to_out(book)


def list_books(session: Session) -> list[BookOut]:
    books = session.scalars(select(Book).join(Book.author).order_by(Book.year, Book.title))
    return [to_out(book) for book in books]


def books_by_author(session: Session, name: str) -> list[BookOut]:
    query = select(Book).join(Book.author).where(Author.name == name).order_by(Book.year)
    return [to_out(book) for book in session.scalars(query)]
