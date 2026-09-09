from collections.abc import Sequence
from datetime import UTC, datetime

from posthog import Posthog

from models import Dvd, EmittedEvent, Rental, RentalCount
from store import Store

SYSTEM_ACTOR = "dvd-rental-backend"


class Analytics:
    def __init__(self, client: Posthog | None, store: Store) -> None:
        self._client = client
        self._store = store

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def _emit(self, event: str, distinct_id: str, properties: dict[str, object]) -> None:
        self._store.record_event(
            EmittedEvent(
                event=event,
                distinct_id=distinct_id,
                properties=properties,
                at=datetime.now(UTC),
            )
        )
        if self._client is not None:
            self._client.capture(event, distinct_id=distinct_id, properties=properties)

    def dvd_rented(self, rental: Rental, dvd: Dvd) -> None:
        self._emit(
            "dvd_rented",
            rental.user_id,
            {
                "rental_id": rental.rental_id,
                "dvd_id": dvd.dvd_id,
                "title": dvd.title,
                "genre": dvd.genre,
                "year": dvd.year,
                "rented_at": rental.rented_at.isoformat(),
                "due_at": rental.due_at.isoformat(),
            },
        )

    def deadline_missed(self, rental: Rental, dvd: Dvd, overdue_seconds: float) -> None:
        seconds = round(overdue_seconds, 3)
        self._emit(
            "dvd_deadline_missed",
            rental.user_id,
            {
                "rental_id": rental.rental_id,
                "dvd_id": dvd.dvd_id,
                "title": dvd.title,
                "due_at": rental.due_at.isoformat(),
                "overdue_seconds": seconds,
                "overdue_minutes": round(seconds / 60, 6),
                "overdue_hours": round(seconds / 3600, 9),
            },
        )

    def idle_rollup(
        self,
        window_minutes: float,
        idle: Sequence[Dvd],
        rented_count: int,
        catalog_size: int,
    ) -> None:
        self._emit(
            "dvds_idle_rollup",
            SYSTEM_ACTOR,
            {
                "window_minutes": window_minutes,
                "window_hours": round(window_minutes / 60, 9),
                "idle_count": len(idle),
                "rented_count": rented_count,
                "catalog_size": catalog_size,
                "idle_dvd_ids": [dvd.dvd_id for dvd in idle],
            },
        )

    def top_rented(self, entries: Sequence[RentalCount]) -> None:
        for rank, entry in enumerate(entries, start=1):
            self._emit(
                "dvd_top_rented",
                SYSTEM_ACTOR,
                {
                    "rank": rank,
                    "dvd_id": entry.dvd.dvd_id,
                    "title": entry.dvd.title,
                    "genre": entry.dvd.genre,
                    "rentals": entry.rentals,
                },
            )

    def never_rented(self, entries: Sequence[Dvd]) -> None:
        for rank, dvd in enumerate(entries, start=1):
            self._emit(
                "dvd_never_rented",
                SYSTEM_ACTOR,
                {
                    "rank": rank,
                    "dvd_id": dvd.dvd_id,
                    "title": dvd.title,
                    "genre": dvd.genre,
                    "rentals": 0,
                },
            )
