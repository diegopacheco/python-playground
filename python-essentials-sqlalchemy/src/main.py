from sqlalchemy import create_engine, String, Integer, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    books: Mapped[list["Book"]] = relationship(back_populates="author")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped[Author] = relationship(back_populates="books")


def main():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        martin = Author(name="Robert Martin")
        martin.books = [Book(title="Clean Code"), Book(title="Clean Architecture")]
        fowler = Author(name="Martin Fowler")
        fowler.books = [Book(title="Refactoring")]
        session.add_all([martin, fowler])
        session.commit()

    with Session(engine) as session:
        print("all books:")
        for book in session.scalars(select(Book).order_by(Book.title)):
            print(f"  {book.title} by {book.author.name}")

        print("filter title like Clean%:")
        query = select(Book).where(Book.title.like("Clean%"))
        for book in session.scalars(query):
            print(f"  {book.title}")

        print("join count per author:")
        for author in session.scalars(select(Author)):
            print(f"  {author.name}: {len(author.books)} book(s)")

        target = session.scalars(select(Book).where(Book.title == "Refactoring")).one()
        target.title = "Refactoring 2nd Edition"
        session.commit()
        print("after update:", target.title)


if __name__ == "__main__":
    main()
