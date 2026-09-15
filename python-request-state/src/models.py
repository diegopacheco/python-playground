from pydantic import BaseModel, ConfigDict, Field


class GameInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    release_year: int = Field(ge=1950, le=2100)
    image_url: str = Field(pattern=r"^https?://\S+$", max_length=2000)


class Game(GameInput):
    id: str
