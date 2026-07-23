from pydantic import BaseModel, Field, ValidationError, field_validator


class Address(BaseModel):
    street: str
    city: str
    zipcode: str = Field(pattern=r"^\d{5}$")


class User(BaseModel):
    id: int
    name: str = Field(min_length=1)
    age: int = Field(ge=0, le=130)
    email: str
    address: Address

    @field_validator("email")
    @classmethod
    def email_must_have_at(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("invalid email")
        return value


def main() -> None:
    user = User(
        id=1,
        name="alice",
        age=30,
        email="alice@example.com",
        address={"street": "1 Main St", "city": "Lisbon", "zipcode": "10001"},
    )
    print("valid user:", user.model_dump())
    print("json:", user.model_dump_json())

    try:
        User(
            id=2,
            name="",
            age=200,
            email="bad",
            address={"street": "x", "city": "y", "zipcode": "abc"},
        )
    except ValidationError as error:
        print("error count:", error.error_count())
        for err in error.errors():
            print(f"  {err['loc']}: {err['msg']}")


if __name__ == "__main__":
    main()
