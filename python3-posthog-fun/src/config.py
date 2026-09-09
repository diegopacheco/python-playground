import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    rental_period_hours: int
    rental_period_seconds: int
    rollup_interval_minutes: float
    deadline_scan_seconds: float
    top_limit: int

    @property
    def rental_period_total_seconds(self) -> float:
        return self.rental_period_hours * 3600 + self.rental_period_seconds


def load_settings() -> Settings:
    return Settings(
        rental_period_hours=int(os.getenv("RENTAL_PERIOD_HOURS", "0")),
        rental_period_seconds=int(os.getenv("RENTAL_PERIOD_SECONDS", "30")),
        rollup_interval_minutes=float(os.getenv("ROLLUP_INTERVAL_MINUTES", "1")),
        deadline_scan_seconds=float(os.getenv("DEADLINE_SCAN_SECONDS", "5")),
        top_limit=int(os.getenv("TOP_LIMIT", "5")),
    )
