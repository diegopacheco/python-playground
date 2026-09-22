import json
from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

WORKLOAD = Path(__file__).parent.parent / "workload"


def run_workload(pytester: pytest.Pytester) -> dict:
    report = pytester.path / "steal.json"
    result = pytester.runpytest_subprocess(
        str(WORKLOAD),
        "-n",
        "2",
        "--dist",
        "worksteal",
        "-p",
        "worksteal.plugin",
        f"--steal-report={report}",
    )
    result.assert_outcomes(passed=16)
    return json.loads(report.read_text())


def test_idle_worker_steals_slow_tests_queued_on_busy_worker(pytester: pytest.Pytester) -> None:
    ledger = run_workload(pytester)
    stolen = [(steal["victim"], test) for steal in ledger["steals"] for test in steal["tests"]]
    assert stolen, "worksteal never moved a queued test to an idle worker"
    for victim, test in stolen:
        assert "slow" in test
        assert ledger["runs"][test] != victim
    assert set(ledger["runs"].values()) == {"gw0", "gw1"}
