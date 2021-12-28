from dataclasses import dataclass
from typing import Optional

from .base import Event


@dataclass(frozen=True)
class CircuitBreakerStateChanged(Event):
    name: str
    state: str
    opened_at: Optional[float]
