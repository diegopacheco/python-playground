import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute
from pydantic import BaseModel
from sqlalchemy import Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/essentials",
)

engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    author: Mapped[str] = mapped_column(String(100))


class BookIn(BaseModel):
    title: str
    author: str


class BookOut(BookIn):
    id: int


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="SQLAlchemy Postgres REST", version="1.0.0", lifespan=lifespan)


@app.get("/")
def root():
    routes = [
        {"path": route.path, "methods": sorted(route.methods)}
        for route in app.routes
        if isinstance(route, APIRoute)
    ]
    routes.append({"path": "/docs", "methods": ["GET"]})
    return {"endpoints": sorted(routes, key=lambda r: r["path"])}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/books", response_model=BookOut)
def create_book(book: BookIn):
    with Session(engine) as session:
        row = Book(title=book.title, author=book.author)
        session.add(row)
        session.commit()
        session.refresh(row)
        return BookOut(id=row.id, title=row.title, author=row.author)


@app.get("/books", response_model=list[BookOut])
def list_books():
    with Session(engine) as session:
        rows = session.scalars(select(Book).order_by(Book.id)).all()
        return [BookOut(id=r.id, title=r.title, author=r.author) for r in rows]


@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int):
    with Session(engine) as session:
        row = session.get(Book, book_id)
        if row is None:
            raise HTTPException(status_code=404, detail="book not found")
        return BookOut(id=row.id, title=row.title, author=row.author)


@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    with Session(engine) as session:
        row = session.get(Book, book_id)
        if row is None:
            raise HTTPException(status_code=404, detail="book not found")
        session.delete(row)
        session.commit()
        return {"deleted": book_id}
