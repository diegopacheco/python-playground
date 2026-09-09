from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class Dvd:
    dvd_id: str
    title: str
    year: int
    genre: str


class RentalStatus(StrEnum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"


@dataclass(slots=True)
class Rental:
    rental_id: str
    dvd_id: str
    user_id: str
    rented_at: datetime
    due_at: datetime
    status: RentalStatus = RentalStatus.ACTIVE
    returned_at: datetime | None = None
    deadline_reported: bool = False

    def overdue_seconds(self, now: datetime) -> float:
        reference = self.returned_at or now
        return max(0.0, (reference - self.due_at).total_seconds())


@dataclass(frozen=True, slots=True)
class RentalCount:
    dvd: Dvd
    rentals: int


@dataclass(frozen=True, slots=True)
class EmittedEvent:
    event: str
    distinct_id: str
    properties: dict[str, object]
    at: datetime
