__lazy_modules__ = ["decimal"]

import decimal
import fractions
import sys


def loaded() -> dict[str, bool]:
    return {name: name in sys.modules for name in ("decimal", "fractions")}


def half() -> decimal.Decimal:
    return decimal.Decimal(1) / 2


def third() -> fractions.Fraction:
    return fractions.Fraction(1, 3)


def main() -> None:
    print(f"before use: {loaded()}")
    print(f"half={half()} third={third()}")
    print(f"after use: {loaded()}")


if __name__ == "__main__":
    main()
