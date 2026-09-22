from pydantic import BaseModel, ConfigDict, Field


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    year: int = Field(ge=1450, le=2100)
    author: str = Field(min_length=1, max_length=120)
    isbn: str | None = Field(default=None, pattern=r"^[0-9-]{10,20}$")


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    year: int
    isbn: str | None
    author_name: str
