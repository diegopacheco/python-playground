from pydantic import BaseModel, ConfigDict, Field


class AuthorIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    pages: int = Field(gt=0)
    price: float = Field(ge=0)
    author: str = Field(min_length=1, max_length=120)


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    pages: int
    price: float
    author_id: int


class LibraryStats(BaseModel):
    books: int
    total_pages: int
    average_price: float
    most_expensive: str | None
