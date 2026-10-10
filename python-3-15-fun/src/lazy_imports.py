import sys
lazy import tomllib


def is_loaded(name: str) -> bool:
    return name in sys.modules


def is_pending(name: str) -> bool:
    return name in sys.lazy_modules


def describe(error: tomllib.TOMLDecodeError) -> str:
    return f"invalid toml: {error}"


def parse(text: str) -> dict[str, object]:
    return tomllib.loads(text)


def main() -> None:
    print(f"before use: loaded={is_loaded('tomllib')} pending={is_pending('tomllib')}")
    print(parse("tool.ruff.target-version = 'py315'"))
    print(f"after use: loaded={is_loaded('tomllib')} pending={is_pending('tomllib')}")


if __name__ == "__main__":
    main()
