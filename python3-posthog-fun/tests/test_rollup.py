import pytest
from conftest import events_named

from rollup import RollupJob


def test_rollup_reports_how_many_dvds_were_not_rented_in_the_window(
    service, store, settings, analytics
):
    service.rent("dvd-002", "diego")

    RollupJob(store, settings, analytics).run()

    event = events_named(store, "dvds_idle_rollup")[0]
    assert event["catalog_size"] == len(store.catalog())
    assert event["rented_count"] == 1
    assert event["idle_count"] == len(store.catalog()) - 1
    assert event["window_minutes"] == settings.rollup_interval_minutes


def test_rollup_publishes_the_window_in_hours_and_minutes(store, settings, analytics):
    RollupJob(store, settings, analytics).run()

    event = events_named(store, "dvds_idle_rollup")[0]
    assert event["window_minutes"] == settings.rollup_interval_minutes
    assert event["window_hours"] == pytest.approx(settings.rollup_interval_minutes / 60)


def test_rollup_publishes_ranked_top_and_never_rented_counters(
    service, store, settings, analytics
):
    for _ in range(2):
        rental = service.rent("dvd-002", "diego")
        service.give_back(rental.rental_id)

    RollupJob(store, settings, analytics).run()

    top = events_named(store, "dvd_top_rented")
    assert [event["rank"] for event in top] == [1]
    assert top[0]["dvd_id"] == "dvd-002"
    assert top[0]["rentals"] == 2

    never = events_named(store, "dvd_never_rented")
    assert [event["rank"] for event in never] == [1, 2, 3, 4, 5]
    assert all(event["rentals"] == 0 for event in never)


def test_rollup_on_an_untouched_catalog_reports_everything_idle(store, settings, analytics):
    RollupJob(store, settings, analytics).run()

    event = events_named(store, "dvds_idle_rollup")[0]
    assert event["idle_count"] == len(store.catalog())
    assert event["rented_count"] == 0
