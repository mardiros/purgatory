"""
Circuit breaker state model.

The state model is implemented using the State pattern from the Gang Of Four.
"""
import abc
import time
from dataclasses import dataclass
from types import TracebackType
from typing import Optional, Type

from purgatory.typing import CircuitBreakerName, StateName


class CircuitBreaker:
    def __init__(self, name: CircuitBreakerName, threshold: int, ttl: float) -> None:
        self.name = name
        self.ttl = ttl
        self.threshold = threshold
        self._state = ClosedState()
        self._dirty = False

    @property
    def state(self) -> StateName:
        return self._state.__class__.__name__

    @property
    def dirty(self) -> bool:
        """True if the state of the circuit breaker has been updated."""
        return self._dirty

    @property
    def opened_at(self) -> Optional[float]:
        return self._state.opened_at

    @property
    def failure_count(self) -> Optional[int]:
        return self._state.failure_count

    def set_state(self, state: "State"):
        self._state = state
        self._dirty = True

    def handle_new_request(self):
        self._state.handle_new_request(self)

    def handle_exception(self, exc: BaseException):
        self._state.handle_exception(self, exc)

    def handle_end_request(self):
        self._state.handle_end_request(self)

    def __enter__(self) -> "CircuitBreaker":
        self.handle_new_request()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        if exc:
            return self.handle_exception(exc)
        else:
            return self.handle_end_request()

    def __repr__(self) -> str:
        return (
            f"<CircuitBreaker "
            f'name="{self.name}" '
            f'state="{self.state}" '
            f'threshold="{self.threshold}" ttl="{self.ttl}">'
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, CircuitBreaker)
            and self.name == other.name
            and self.threshold == other.threshold
            and self.ttl == other.ttl
        )


@dataclass
class State(abc.ABC):
    failure_count: Optional[int] = None
    opened_at: Optional[float] = None

    @abc.abstractmethod
    def handle_new_request(self, context: CircuitBreaker):
        """Handle new code block"""

    @abc.abstractmethod
    def handle_exception(self, context: CircuitBreaker, exc: BaseException):
        """Handle exception during the code block"""

    @abc.abstractmethod
    def handle_end_request(self, context: CircuitBreaker):
        """Handle proper execution after the code block"""

    def __eq__(self, other: object) -> bool:
        return self.__class__ == other.__class__


class ClosedState(State):
    """In closed state, track for failure."""

    failure_count: int

    def __init__(self) -> None:
        self.failure_count = 0

    def handle_new_request(self, context: CircuitBreaker):
        """When the circuit is closed, the new request has no incidence"""

    def handle_exception(self, context: CircuitBreaker, exc: BaseException):
        self.failure_count += 1
        if self.failure_count >= context.threshold:
            opened = OpenedState()
            context.set_state(opened)

    def handle_end_request(self, context: CircuitBreaker):
        """Reset in case the request is ok"""
        self.failure_count = 0


class OpenedState(State, Exception):
    """In open state, reopen after a TTL."""

    opened_at: float

    def __init__(self) -> None:
        Exception.__init__(self, "Circuit breaker is open")
        self.opened_at = time.time()

    def handle_new_request(self, context: CircuitBreaker):
        closed_at = self.opened_at + context.ttl
        if time.time() > closed_at:
            context.set_state(HalfOpenedState())
            return context.handle_new_request()
        raise self

    def handle_exception(self, exc: BaseException):
        """
        When the circuit is opened, the OpenState is raised before entering.

        this function is never called.
        """

    def handle_end_request(self):
        """
        When the circuit is opened, the OpenState is raised before entering.

        this function is never called.
        """


class HalfOpenedState(State):
    """In half open state, decide to reopen or to close."""

    def handle_new_request(self, context: CircuitBreaker):
        """In half open state, we check the result of the code block execution."""

    def handle_exception(self, context: CircuitBreaker, exc: BaseException):
        opened = OpenedState()
        context.set_state(opened)

    def handle_end_request(self, context: CircuitBreaker):
        context.set_state(ClosedState())
