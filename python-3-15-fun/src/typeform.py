from types import UnionType
from typing import TypeForm, cast


def trycast[T](typx: TypeForm[T], value: object) -> T | None:
    form: object = typx
    if isinstance(form, type | UnionType) and isinstance(value, form):
        return cast(T, value)
    return None


def main() -> None:
    print(f"str | None with 'hi': {trycast(str | None, 'hi')!r}")
    print(f"int with 'hi': {trycast(int, 'hi')!r}")
    print(f"int | float with 2.5: {trycast(int | float, 2.5)!r}")


if __name__ == "__main__":
    main()
