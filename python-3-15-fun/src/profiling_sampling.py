import subprocess
import sys
from collections import Counter
from pathlib import Path

REPORT = Path(__file__).resolve().parent.parent / ".run" / "flamegraph.html"


def molecules(count: int) -> list[list[str]]:
    return [["C", "H", "H", "O", "N"] for _ in range(count)]


def count_elements(symbols: list[list[str]]) -> Counter[str]:
    return Counter(sum(symbols, []))


def profile(report: Path) -> subprocess.CompletedProcess[str]:
    report.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "profiling.sampling", "run", "--flamegraph", "-o", str(report), __file__, "workload"]
    return subprocess.run(command, check=False, capture_output=True, text=True)


def main() -> None:
    if sys.argv[1:] == ["workload"]:
        print(count_elements(molecules(15_000)))
        return
    result = profile(REPORT)
    print(result.stdout + result.stderr)
    if result.returncode != 0 or not REPORT.exists():
        raise SystemExit("Tachyon could not sample the workload")
    print(f"flame graph written to {REPORT.relative_to(REPORT.parent.parent)}")


if __name__ == "__main__":
    main()
