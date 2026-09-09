from models import Dvd

CATALOG: tuple[Dvd, ...] = (
    Dvd("dvd-001", "Blade Runner", 1982, "sci-fi"),
    Dvd("dvd-002", "The Matrix", 1999, "sci-fi"),
    Dvd("dvd-003", "Fight Club", 1999, "drama"),
    Dvd("dvd-004", "Pulp Fiction", 1994, "crime"),
    Dvd("dvd-005", "Alien", 1979, "horror"),
    Dvd("dvd-006", "Heat", 1995, "crime"),
    Dvd("dvd-007", "Akira", 1988, "animation"),
    Dvd("dvd-008", "The Thing", 1982, "horror"),
    Dvd("dvd-009", "Goodfellas", 1990, "crime"),
    Dvd("dvd-010", "Ghost in the Shell", 1995, "animation"),
)
