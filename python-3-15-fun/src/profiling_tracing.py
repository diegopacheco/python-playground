from profiling.tracing import Profile
from types import CodeType


def fibonacci(n: int) -> int:
    return n if n < 2 else fibonacci(n - 1) + fibonacci(n - 2)


def call_count(n: int) -> int:
    profile = Profile()
    profile.enable()
    fibonacci(n)
    profile.disable()
    return next(
        entry.callcount
        for entry in profile.getstats()
        if isinstance(entry.code, CodeType) and entry.code.co_name == "fibonacci"
    )


def main() -> None:
    print(f"fibonacci(10) traced calls: {call_count(10)}")


if __name__ == "__main__":
    main()
