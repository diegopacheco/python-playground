import fire


class Calculator:
    def add(self, a: float, b: float) -> float:
        return a + b

    def sub(self, a: float, b: float) -> float:
        return a - b

    def mul(self, a: float, b: float) -> float:
        return a * b

    def div(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("division by zero")
        return a / b


def main() -> None:
    fire.Fire(Calculator)


if __name__ == "__main__":
    main()
