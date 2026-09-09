from datetime import datetime

from pydantic import BaseModel


class RentRequest(BaseModel):
    dvd_id: str
    user_id: str


class DvdOut(BaseModel):
    dvd_id: str
    title: str
    year: int
    genre: str
    available: bool


class RentalOut(BaseModel):
    rental_id: str
    dvd_id: str
    title: str
    user_id: str
    rented_at: datetime
    due_at: datetime
    status: str
    returned_at: datetime | None
    overdue_seconds: float


class RankedDvdOut(BaseModel):
    rank: int
    dvd_id: str
    title: str
    genre: str
    rentals: int


class EventOut(BaseModel):
    event: str
    distinct_id: str
    properties: dict[str, object]
    at: datetime


class HealthOut(BaseModel):
    status: str
    posthog_enabled: bool
    rental_period_seconds: float
    rollup_interval_minutes: float
    deadline_scan_seconds: float
