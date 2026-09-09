import time

import pytest
from conftest import events_named

from models import RentalStatus
from rentals import DvdNotFound, DvdUnavailable, RentalNotFound


def test_renting_emits_one_counter_event_per_rental(service, store):
    service.rent("dvd-002", "diego")
    service.rent("dvd-004", "diego")

    emitted = events_named(store, "dvd_rented")
    assert len(emitted) == 2
    assert {event["dvd_id"] for event in emitted} == {"dvd-002", "dvd-004"}


def test_rented_event_carries_the_dvd_identity_needed_to_rank_titles(service, store):
    service.rent("dvd-002", "diego")

    event = events_named(store, "dvd_rented")[0]
    assert event["dvd_id"] == "dvd-002"
    assert event["title"] == "The Matrix"


def test_a_dvd_already_out_cannot_be_rented_twice(service, store):
    service.rent("dvd-002", "diego")

    with pytest.raises(DvdUnavailable):
        service.rent("dvd-002", "someone-else")

    assert len(events_named(store, "dvd_rented")) == 1


def test_returning_frees_the_dvd_for_the_next_renter(service):
    rental = service.rent("dvd-002", "diego")
    service.give_back(rental.rental_id)

    assert service.rent("dvd-002", "someone-else").dvd_id == "dvd-002"


def test_unknown_ids_are_rejected(service):
    with pytest.raises(DvdNotFound):
        service.rent("nope", "diego")
    with pytest.raises(RentalNotFound):
        service.give_back("nope")


def test_missing_a_deadline_emits_a_counter_with_hours_and_seconds(service, store):
    service.rent("dvd-002", "diego")
    time.sleep(1.1)

    assert len(service.scan_deadlines()) == 1

    event = events_named(store, "dvd_deadline_missed")[0]
    assert event["dvd_id"] == "dvd-002"
    assert isinstance(event["overdue_seconds"], float)
    assert event["overdue_seconds"] > 0
    assert event["overdue_hours"] == pytest.approx(event["overdue_seconds"] / 3600, rel=1e-3)


def test_a_missed_deadline_is_counted_once_however_often_we_scan(service, store):
    service.rent("dvd-002", "diego")
    time.sleep(1.1)

    service.scan_deadlines()
    service.scan_deadlines()
    service.scan_deadlines()

    assert len(events_named(store, "dvd_deadline_missed")) == 1


def test_a_rental_returned_before_its_deadline_never_counts_as_missed(service, store):
    rental = service.rent("dvd-002", "diego")
    service.give_back(rental.rental_id)
    time.sleep(1.1)

    service.scan_deadlines()

    assert events_named(store, "dvd_deadline_missed") == []
    assert store.rental(rental.rental_id).status is RentalStatus.RETURNED


def test_an_overdue_rental_stays_overdue_after_it_is_returned(service, store):
    rental = service.rent("dvd-002", "diego")
    time.sleep(1.1)
    service.scan_deadlines()

    service.give_back(rental.rental_id)

    assert store.rental(rental.rental_id).status is RentalStatus.OVERDUE
