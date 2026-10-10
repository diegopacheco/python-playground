import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class BuildInfo:
    version: str
    compiler: str
    system: str
    machine: str


def build_info() -> BuildInfo:
    return BuildInfo(
        platform.python_version(),
        platform.python_compiler(),
        platform.system(),
        platform.machine(),
    )


def main() -> None:
    info = build_info()
    print(f"python {info.version} built with {info.compiler} for {info.system} {info.machine}")


if __name__ == "__main__":
    main()
