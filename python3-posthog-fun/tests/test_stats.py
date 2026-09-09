from datetime import UTC, datetime, timedelta

from stats import idle_since, never_rented, top_rented


def test_top_rented_ranks_by_how_often_a_title_went_out(service, store):
    for _ in range(3):
        rental = service.rent("dvd-002", "diego")
        service.give_back(rental.rental_id)
    rental = service.rent("dvd-004", "diego")
    service.give_back(rental.rental_id)

    ranked = top_rented(store, limit=5)

    assert [(entry.dvd.dvd_id, entry.rentals) for entry in ranked] == [
        ("dvd-002", 3),
        ("dvd-004", 1),
    ]


def test_top_rented_never_returns_more_than_the_requested_limit(service, store):
    for dvd in store.catalog():
        service.rent(dvd.dvd_id, "diego")

    assert len(top_rented(store, limit=5)) == 5


def test_never_rented_lists_only_titles_with_no_rental_at_all(service, store):
    service.rent("dvd-002", "diego")

    ids = {dvd.dvd_id for dvd in never_rented(store, limit=10)}

    assert "dvd-002" not in ids
    assert "dvd-001" in ids


def test_a_returned_title_is_still_not_a_never_rented_title(service, store):
    rental = service.rent("dvd-002", "diego")
    service.give_back(rental.rental_id)

    assert "dvd-002" not in {dvd.dvd_id for dvd in never_rented(store, limit=10)}


def test_idle_counts_titles_untouched_during_the_rollup_window(service, store):
    service.rent("dvd-002", "diego")

    window_start = datetime.now(UTC) - timedelta(minutes=1)
    idle = idle_since(store, window_start)

    assert "dvd-002" not in {dvd.dvd_id for dvd in idle}
    assert len(idle) == len(store.catalog()) - 1


def test_a_title_rented_before_the_window_and_already_back_counts_as_idle(service, store):
    rental = service.rent("dvd-002", "diego")
    service.give_back(rental.rental_id)

    window_start = datetime.now(UTC) + timedelta(minutes=1)
    idle = idle_since(store, window_start)

    assert "dvd-002" in {dvd.dvd_id for dvd in idle}
