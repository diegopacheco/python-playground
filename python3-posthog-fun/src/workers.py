import threading
from collections.abc import Callable


class IntervalWorker:
    def __init__(self, name: str, interval_seconds: float, job: Callable[[], object]) -> None:
        self._name = name
        self._interval_seconds = interval_seconds
        self._job = job
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, name=name, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=self._interval_seconds + 1)

    def _loop(self) -> None:
        while not self._stop.wait(self._interval_seconds):
            try:
                self._job()
            except Exception as error:
                print(f"[{self._name}] job failed: {error!r}")
