from library.repository import add_book
from library.schemas import BookIn, BookOut


def year_label(book: BookOut) -> str:
    return book.year


def titles(books: list[BookOut]) -> list[int]:
    return [b.title for b in books]


def save(data: BookIn) -> BookOut:
    return add_book(data)
