from typing import TypedDict


class Point2D(TypedDict, closed=True):
    x: int
    y: int


def total(point: Point2D) -> int:
    return sum(point.values())


def main() -> None:
    point = Point2D(x=3, y=4)
    print(f"closed={Point2D.__closed__} total={total(point)}")


if __name__ == "__main__":
    main()
