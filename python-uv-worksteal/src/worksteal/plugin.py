import json
from collections.abc import Sequence
from pathlib import Path

import pytest
from _pytest.terminal import TerminalReporter
from xdist.remote import Producer
from xdist.scheduler import WorkStealingScheduling
from xdist.workermanage import WorkerController


class StealLedger:
    def __init__(self) -> None:
        self.steals: list[dict[str, object]] = []
        self.runs: dict[str, str] = {}

    def record_steal(self, victim: str, tests: list[str]) -> None:
        if tests:
            self.steals.append({"victim": victim, "tests": tests})

    def record_run(self, test: str, worker: str) -> None:
        self.runs[test] = worker

    def to_dict(self) -> dict[str, object]:
        return {"steals": self.steals, "runs": self.runs}


LEDGER = pytest.StashKey[StealLedger]()


class RecordingWorkStealing(WorkStealingScheduling):
    def __init__(self, config: pytest.Config, log: Producer, ledger: StealLedger) -> None:
        super().__init__(config, log)
        self.ledger = ledger

    def remove_pending_tests_from_node(
        self, node: WorkerController, indices: Sequence[int]
    ) -> None:
        collection = self.collection or []
        self.ledger.record_steal(node.gateway.id, [collection[i] for i in indices])
        super().remove_pending_tests_from_node(node, indices)


def is_controller(config: pytest.Config) -> bool:
    return not hasattr(config, "workerinput")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--steal-report", default=None, help="write work stealing ledger as JSON")


def pytest_configure(config: pytest.Config) -> None:
    config.stash[LEDGER] = StealLedger()


def pytest_xdist_make_scheduler(
    config: pytest.Config, log: Producer
) -> WorkStealingScheduling | None:
    if config.getoption("dist") != "worksteal":
        return None
    return RecordingWorkStealing(config, log, config.stash[LEDGER])


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    node = getattr(report, "node", None)
    if report.when == "call" and isinstance(node, WorkerController):
        config = node.config
        config.stash[LEDGER].record_run(report.nodeid, node.gateway.id)


def pytest_terminal_summary(terminalreporter: TerminalReporter, config: pytest.Config) -> None:
    if not is_controller(config):
        return
    ledger = config.stash[LEDGER]
    terminalreporter.section("work stealing evidence")
    if not ledger.steals:
        terminalreporter.write_line("no steals recorded")
    for steal in ledger.steals:
        victim = str(steal["victim"])
        tests = steal["tests"]
        assert isinstance(tests, list)
        for test in tests:
            thief = ledger.runs.get(test, "?")
            terminalreporter.write_line(f"{test}  queued on {victim}  stolen and run by {thief}")
    terminalreporter.write_line(f"steal events: {len(ledger.steals)}")


def pytest_sessionfinish(session: pytest.Session) -> None:
    config = session.config
    path = config.getoption("steal_report")
    if path and is_controller(config):
        Path(path).write_text(json.dumps(config.stash[LEDGER].to_dict(), indent=2))
