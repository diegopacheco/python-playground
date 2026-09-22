from sqlalchemy import select
from sqlalchemy.orm import Session

from library import stats
from library.models import Author, Book
from library.schemas import AuthorIn, BookIn, BookOut, LibraryStats


def get_or_create_author(session: Session, data: AuthorIn) -> Author:
    author = session.scalars(select(Author).where(Author.name == data.name)).first()
    if author is None:
        author = Author(name=data.name)
        session.add(author)
        session.flush()
    return author


def add_book(session: Session, data: BookIn) -> BookOut:
    author = get_or_create_author(session, AuthorIn(name=data.author))
    book = Book(title=data.title, pages=data.pages, price=data.price, author_id=author.id)
    session.add(book)
    session.commit()
    return BookOut.model_validate(book)


def list_books(session: Session) -> list[BookOut]:
    books = session.scalars(select(Book).order_by(Book.id)).all()
    return [BookOut.model_validate(book) for book in books]


def library_stats(session: Session) -> LibraryStats:
    books = list_books(session)
    return LibraryStats(
        books=len(books),
        total_pages=stats.total_pages([b.pages for b in books]),
        average_price=stats.average_price([b.price for b in books]),
        most_expensive=stats.most_expensive([b.title for b in books], [b.price for b in books]),
    )
