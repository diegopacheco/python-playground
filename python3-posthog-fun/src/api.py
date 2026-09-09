from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from analytics import Analytics
from config import Settings
from models import Rental
from rentals import DvdNotFound, DvdUnavailable, RentalNotFound, RentalService
from schemas import (
    DvdOut,
    EventOut,
    HealthOut,
    RankedDvdOut,
    RentalOut,
    RentRequest,
    VisitRequest,
)
from stats import never_rented, top_rented
from store import Store


def build_router(
    store: Store,
    settings: Settings,
    service: RentalService,
    analytics: Analytics,
) -> APIRouter:
    router = APIRouter()

    def to_rental_out(rental: Rental) -> RentalOut:
        dvd = store.dvd(rental.dvd_id)
        return RentalOut(
            rental_id=rental.rental_id,
            dvd_id=rental.dvd_id,
            title=dvd.title if dvd else rental.dvd_id,
            user_id=rental.user_id,
            rented_at=rental.rented_at,
            due_at=rental.due_at,
            status=rental.status.value,
            returned_at=rental.returned_at,
            overdue_seconds=round(rental.overdue_seconds(datetime.now(UTC)), 3),
        )

    @router.get("/health")
    def health() -> HealthOut:
        return HealthOut(
            status="ok",
            posthog_enabled=analytics.enabled,
            rental_period_seconds=settings.rental_period_total_seconds,
            rollup_interval_minutes=settings.rollup_interval_minutes,
            deadline_scan_seconds=settings.deadline_scan_seconds,
        )

    @router.post("/visits", status_code=202)
    def record_visit(request: VisitRequest) -> dict[str, str]:
        analytics.app_opened(request.user_id)
        return {"status": "recorded"}

    @router.get("/dvds")
    def list_dvds() -> list[DvdOut]:
        return [
            DvdOut(
                dvd_id=dvd.dvd_id,
                title=dvd.title,
                year=dvd.year,
                genre=dvd.genre,
                available=store.active_rental_for(dvd.dvd_id) is None,
            )
            for dvd in store.catalog()
        ]

    @router.post("/rentals", status_code=201)
    def rent(request: RentRequest) -> RentalOut:
        try:
            return to_rental_out(service.rent(request.dvd_id, request.user_id))
        except DvdNotFound:
            raise HTTPException(status_code=404, detail=f"unknown dvd {request.dvd_id}")
        except DvdUnavailable:
            raise HTTPException(status_code=409, detail=f"dvd {request.dvd_id} is already rented")

    @router.post("/rentals/{rental_id}/return")
    def give_back(rental_id: str) -> RentalOut:
        try:
            return to_rental_out(service.give_back(rental_id))
        except RentalNotFound:
            raise HTTPException(status_code=404, detail=f"unknown rental {rental_id}")

    @router.get("/rentals")
    def list_rentals() -> list[RentalOut]:
        return [to_rental_out(rental) for rental in store.rentals()]

    @router.get("/stats/top-rented")
    def stats_top_rented() -> list[RankedDvdOut]:
        return [
            RankedDvdOut(
                rank=rank,
                dvd_id=entry.dvd.dvd_id,
                title=entry.dvd.title,
                genre=entry.dvd.genre,
                rentals=entry.rentals,
            )
            for rank, entry in enumerate(top_rented(store, settings.top_limit), start=1)
        ]

    @router.get("/stats/never-rented")
    def stats_never_rented() -> list[RankedDvdOut]:
        return [
            RankedDvdOut(
                rank=rank,
                dvd_id=dvd.dvd_id,
                title=dvd.title,
                genre=dvd.genre,
                rentals=0,
            )
            for rank, dvd in enumerate(never_rented(store, settings.top_limit), start=1)
        ]

    @router.get("/events")
    def list_events() -> list[EventOut]:
        return [
            EventOut(
                event=event.event,
                distinct_id=event.distinct_id,
                properties=event.properties,
                at=event.at,
            )
            for event in store.events()
        ]

    return router
