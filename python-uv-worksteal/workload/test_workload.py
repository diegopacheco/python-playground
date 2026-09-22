import time

import pytest

SLOW = [pytest.param(0.5, id=f"slow-{i}") for i in range(8)]
FAST = [pytest.param(0.01, id=f"fast-{i}") for i in range(8)]


@pytest.mark.parametrize("seconds", SLOW + FAST)
def test_job(seconds: float) -> None:
    time.sleep(seconds)
    assert seconds > 0
