import os
import subprocess
import sys

PROBE = "import sys, decimal; print(sys.get_lazy_imports(), 'decimal' in sys.modules)"


def probe(flags: list[str], env: dict[str, str]) -> str:
    result = subprocess.run(
        [sys.executable, *flags, "-c", PROBE],
        env=os.environ | env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main() -> None:
    print(f"default: {probe([], {})}")
    print(f"-X lazy_imports=all: {probe(['-X', 'lazy_imports=all'], {})}")
    print(f"PYTHON_LAZY_IMPORTS=all: {probe([], {'PYTHON_LAZY_IMPORTS': 'all'})}")


if __name__ == "__main__":
    main()
