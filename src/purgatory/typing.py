from typing import Callable

from purgatory.domain.messages.base import Event


CircuitBreakerName = str
TTL = float
Threshold = int


try:
    from typing import Literal

    StateName = Literal["opened", "closed", "half-opened"]
    Hook = Callable[
        [
            CircuitBreakerName,
            Literal["circuit_breaker_created", "state_changed", "failed", "recovered"],
            Event,
        ],
        None,
    ]

except ImportError:
    StateName = str
    EventType = str
    Hook = Callable[
        [
            CircuitBreakerName,
            str,
            Event,
        ],
        None,
    ]
