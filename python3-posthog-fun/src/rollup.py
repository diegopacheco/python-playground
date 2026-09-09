from datetime import UTC, datetime, timedelta

from analytics import Analytics
from config import Settings
from stats import idle_since, never_rented, top_rented
from store import Store


class RollupJob:
    def __init__(self, store: Store, settings: Settings, analytics: Analytics) -> None:
        self._store = store
        self._settings = settings
        self._analytics = analytics

    def run(self) -> None:
        catalog_size = len(self._store.catalog())
        window_start = datetime.now(UTC) - timedelta(
            minutes=self._settings.rollup_interval_minutes
        )
        idle = idle_since(self._store, window_start)

        self._analytics.idle_rollup(
            window_minutes=self._settings.rollup_interval_minutes,
            idle=idle,
            rented_count=catalog_size - len(idle),
            catalog_size=catalog_size,
        )
        self._analytics.top_rented(top_rented(self._store, self._settings.top_limit))
        self._analytics.never_rented(never_rented(self._store, self._settings.top_limit))
