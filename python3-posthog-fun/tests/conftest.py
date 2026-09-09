import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics import Analytics
from catalog import CATALOG
from config import Settings
from rentals import RentalService
from store import Store


@pytest.fixture
def settings() -> Settings:
    return Settings(
        rental_period_hours=0,
        rental_period_seconds=1,
        rollup_interval_minutes=1.0,
        deadline_scan_seconds=0.1,
        top_limit=5,
    )


@pytest.fixture
def store() -> Store:
    return Store(CATALOG)


@pytest.fixture
def analytics(store: Store) -> Analytics:
    return Analytics(None, store)


@pytest.fixture
def service(store: Store, settings: Settings, analytics: Analytics) -> RentalService:
    return RentalService(store, settings, analytics)


def events_named(store: Store, name: str) -> list[dict[str, object]]:
    ordered = reversed(store.events())
    return [event.properties for event in ordered if event.event == name]
