import threading
from collections.abc import Iterable
from datetime import datetime

from models import Dvd, EmittedEvent, Rental, RentalStatus


class Store:
    def __init__(self, catalog: Iterable[Dvd], event_log_size: int = 200) -> None:
        self._lock = threading.RLock()
        self._catalog: dict[str, Dvd] = {dvd.dvd_id: dvd for dvd in catalog}
        self._rentals: dict[str, Rental] = {}
        self._events: list[EmittedEvent] = []
        self._event_log_size = event_log_size

    def catalog(self) -> list[Dvd]:
        with self._lock:
            return list(self._catalog.values())

    def dvd(self, dvd_id: str) -> Dvd | None:
        with self._lock:
            return self._catalog.get(dvd_id)

    def rentals(self) -> list[Rental]:
        with self._lock:
            return list(self._rentals.values())

    def rental(self, rental_id: str) -> Rental | None:
        with self._lock:
            return self._rentals.get(rental_id)

    def active_rental_for(self, dvd_id: str) -> Rental | None:
        with self._lock:
            return self._active_rental_for(dvd_id)

    def _active_rental_for(self, dvd_id: str) -> Rental | None:
        for rental in self._rentals.values():
            if rental.dvd_id == dvd_id and rental.returned_at is None:
                return rental
        return None

    def start_rental(self, rental: Rental) -> bool:
        with self._lock:
            if self._active_rental_for(rental.dvd_id) is not None:
                return False
            self._rentals[rental.rental_id] = rental
            return True

    def mark_returned(self, rental_id: str, returned_at: datetime) -> Rental | None:
        with self._lock:
            rental = self._rentals.get(rental_id)
            if rental is None or rental.returned_at is not None:
                return None
            rental.returned_at = returned_at
            if rental.status is not RentalStatus.OVERDUE:
                rental.status = RentalStatus.RETURNED
            return rental

    def claim_missed_deadlines(self, now: datetime) -> list[Rental]:
        with self._lock:
            missed: list[Rental] = []
            for rental in self._rentals.values():
                if rental.deadline_reported or rental.returned_at is not None:
                    continue
                if now < rental.due_at:
                    continue
                rental.deadline_reported = True
                rental.status = RentalStatus.OVERDUE
                missed.append(rental)
            return missed

    def record_event(self, event: EmittedEvent) -> None:
        with self._lock:
            self._events.append(event)
            overflow = len(self._events) - self._event_log_size
            if overflow > 0:
                del self._events[:overflow]

    def events(self) -> list[EmittedEvent]:
        with self._lock:
            return list(reversed(self._events))
