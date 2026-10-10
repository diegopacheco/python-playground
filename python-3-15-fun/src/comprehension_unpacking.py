lazy from collections.abc import Iterator


def flatten[T](rows: list[list[T]]) -> list[T]:
    return [*row for row in rows]


def unique[T](rows: list[list[T]]) -> set[T]:
    return {*row for row in rows}


def merge[K, V](maps: list[dict[K, V]]) -> dict[K, V]:
    return {**mapping for mapping in maps}


def stream[T](rows: list[list[T]]) -> Iterator[T]:
    return (*row for row in rows)


def main() -> None:
    rows = [[1, 2, 3], [3, 4], [5]]
    print(f"flatten={flatten(rows)}")
    print(f"unique={unique(rows)}")
    print(f"merge={merge([{'a': 1}, {'b': 2}, {'a': 3}])}")
    print(f"stream={list(stream(rows))}")


if __name__ == "__main__":
    main()
