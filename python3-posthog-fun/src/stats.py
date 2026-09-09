from collections import Counter
from datetime import datetime

from models import Dvd, RentalCount
from store import Store


def rental_counts(store: Store) -> Counter[str]:
    return Counter(rental.dvd_id for rental in store.rentals())


def top_rented(store: Store, limit: int) -> list[RentalCount]:
    counts = rental_counts(store)
    ranked: list[RentalCount] = []
    for dvd_id, total in counts.most_common():
        dvd = store.dvd(dvd_id)
        if dvd is not None:
            ranked.append(RentalCount(dvd=dvd, rentals=total))
    return ranked[:limit]


def never_rented(store: Store, limit: int) -> list[Dvd]:
    counts = rental_counts(store)
    return [dvd for dvd in store.catalog() if counts[dvd.dvd_id] == 0][:limit]


def idle_since(store: Store, window_start: datetime) -> list[Dvd]:
    active = {
        rental.dvd_id
        for rental in store.rentals()
        if rental.rented_at >= window_start or rental.returned_at is None
    }
    return [dvd for dvd in store.catalog() if dvd.dvd_id not in active]
