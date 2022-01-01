from dataclasses import dataclass
from typing import Optional

from purgatory.typing import TTL, StateName, Threshold

from .base import Event


@dataclass(frozen=True)
class CircuitBreakerCreated(Event):
    name: str
    threshold: Threshold
    ttl: TTL


@dataclass(frozen=True)
class ContextChanged(Event):
    name: str
    state: StateName
    opened_at: Optional[float]


@dataclass(frozen=True)
class CircuitBreakerFailed(Event):
    name: str
    failure_count: int


@dataclass(frozen=True)
class CircuitBreakerRecovered(Event):
    name: str
