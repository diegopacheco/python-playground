from datetime import UTC, datetime, timedelta
from uuid import uuid4

from analytics import Analytics
from config import Settings
from models import Rental
from store import Store


class DvdNotFound(Exception):
    pass


class DvdUnavailable(Exception):
    pass


class RentalNotFound(Exception):
    pass


class RentalService:
    def __init__(self, store: Store, settings: Settings, analytics: Analytics) -> None:
        self._store = store
        self._settings = settings
        self._analytics = analytics

    def rent(self, dvd_id: str, user_id: str) -> Rental:
        dvd = self._store.dvd(dvd_id)
        if dvd is None:
            raise DvdNotFound(dvd_id)

        now = datetime.now(UTC)
        rental = Rental(
            rental_id=uuid4().hex,
            dvd_id=dvd_id,
            user_id=user_id,
            rented_at=now,
            due_at=now + timedelta(seconds=self._settings.rental_period_total_seconds),
        )
        if not self._store.start_rental(rental):
            raise DvdUnavailable(dvd_id)

        self._analytics.dvd_rented(rental, dvd)
        return rental

    def give_back(self, rental_id: str) -> Rental:
        if self._store.rental(rental_id) is None:
            raise RentalNotFound(rental_id)
        rental = self._store.mark_returned(rental_id, datetime.now(UTC))
        if rental is None:
            raise RentalNotFound(rental_id)
        return rental

    def scan_deadlines(self) -> list[Rental]:
        now = datetime.now(UTC)
        missed = self._store.claim_missed_deadlines(now)
        for rental in missed:
            dvd = self._store.dvd(rental.dvd_id)
            if dvd is not None:
                self._analytics.deadline_missed(rental, dvd, rental.overdue_seconds(now))
        return missed
