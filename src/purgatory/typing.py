from typing import Callable

from typing_extensions import Literal

from purgatory.domain.messages.base import Event

CircuitName = str
TTL = float
Threshold = int


StateName = Literal["opened", "closed", "half-opened"]
Hook = Callable[
    [
        CircuitName,
        Literal["circuit_breaker_created", "state_changed", "failed", "recovered"],
        Event,
    ],
    None,
]
