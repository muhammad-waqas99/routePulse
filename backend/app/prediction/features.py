"""Feature engineering for the prediction models.

Converts raw inputs (time, day, class schedule, events) into model features.
All deterministic and dependency-free.
"""
from __future__ import annotations

                                                         
BUCKET_MINUTES = 5


def time_bucket(time_min: int, bucket_size: int = BUCKET_MINUTES) -> int:
    """Return the start (minutes from midnight) of the bucket containing time_min."""
    return (time_min // bucket_size) * bucket_size


def day_type(iso_weekday: int) -> str:
    """Map ISO weekday (1=Monday..7=Sunday) to WEEKDAY or WEEKEND."""
    return "WEEKEND" if iso_weekday >= 6 else "WEEKDAY"


def is_class_change(time_min: int, class_change_minutes: list[int]) -> bool:
    """True if time_min falls on or just after a class-change boundary.

    Class-change boundaries are treated as one-bucket events.
    """
    for c in class_change_minutes:
        if c <= time_min < c + BUCKET_MINUTES:
            return True
    return False
