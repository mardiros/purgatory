from dataclasses import dataclass
from typing import Any, List

from .base import Event


@dataclass(frozen=True)
class TimeSlotChanged(Event):
    slots: List[int]


@dataclass(frozen=True)
class AlertStateChanged(Event):
    rule_name: str
    """Name of the alert rule."""
    timeslot: int
    """Changed time of the alert."""
    probe_success: bool
    """True: alert is closed, False: alert is opened."""
    threshold: float
    """Configured threshold of the alert."""
    hits: float
    """Last probe value of the alert."""
    interval: int
    """Last probe value of the alert."""


@dataclass(frozen=True)
class LogLineAdded(Event):
    logline: Any  # type LogLine but it is not importable here


@dataclass(frozen=True)
class EOF(Event):
    date: int
