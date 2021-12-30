from dataclasses import dataclass
from typing import Optional

from .base import Event


@dataclass(frozen=True)
class CircuitBreakerStateChanged(Event):
    name: str
    state: str
    opened_at: Optional[float]


@dataclass(frozen=True)
class CircuitBreakerFailed(Event):
    name: str
    failure_count: int


@dataclass(frozen=True)
class CircuitBreakerRecovered(Event):
    name: str
