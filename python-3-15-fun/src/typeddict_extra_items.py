from typing import TypedDict


class Point(TypedDict, extra_items=int):
    x: int
    y: int


def total(point: Point) -> int:
    return sum(point.values())


def main() -> None:
    point = Point(x=3, y=4, z=5)
    print(f"extra_items={Point.__extra_items__.__name__} total={total(point)}")


if __name__ == "__main__":
    main()
