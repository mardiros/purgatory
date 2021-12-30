"""
Circuit breaker state model.

The state model is implemented using the State pattern from the Gang Of Four.
"""
import abc
import time
from dataclasses import dataclass
from types import TracebackType
from typing import List, Optional, Type

from purgatory.domain.messages.base import Event
from purgatory.domain.messages.events import (
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    CircuitBreakerStateChanged,
)
from purgatory.typing import CircuitBreakerName, StateName


class CircuitBreaker:
    name: CircuitBreakerName
    threshold: int
    ttl: float
    messages: List[Event]
    exclude_list: List[Type[Exception]]

    def __init__(
        self,
        name: CircuitBreakerName,
        threshold: int,
        ttl: float,
        state="closed",
        failure_count: int = 0,
        opened_at: Optional[float] = None,
        exclude: Optional[List[Type[Exception]]] = None,
    ) -> None:
        self.name = name
        self.ttl = ttl
        self.threshold = threshold

        self._state = {
            ClosedState.name: ClosedState,
            OpenedState.name: OpenedState,
            HalfOpenedState.name: HalfOpenedState,
        }[state]()
        self._state.opened_at = opened_at
        self._state.failure_count = failure_count
        self.messages = []
        self.exclude_list = exclude or []

    @property
    def state(self) -> StateName:
        return self._state.name

    @property
    def opened_at(self) -> Optional[float]:
        return self._state.opened_at

    @property
    def failure_count(self) -> Optional[int]:
        return self._state.failure_count

    def set_state(self, state: "State"):
        self._state = state
        self.messages.append(
            CircuitBreakerStateChanged(
                self.name,
                self.state,
                state.opened_at,
            )
        )

    def mark_failure(self, failure_count):
        self.messages.append(
            CircuitBreakerFailed(
                self.name,
                failure_count,
            )
        )

    def recover_failure(self):
        self.messages.append(
            CircuitBreakerRecovered(
                self.name,
            )
        )

    def handle_new_request(self):
        self._state.handle_new_request(self)

    def handle_exception(self, exc: BaseException):
        failed = True
        for exctype in self.exclude_list:
            if isinstance(exc, exctype):
                failed = False
                break
        if failed:
            self._state.handle_exception(self, exc)
        else:
            self._state.handle_end_request(self)

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
    name: str = ""

    @abc.abstractmethod
    def handle_new_request(self, context: CircuitBreaker):
        """Handle new code block"""

    @abc.abstractmethod
    def handle_exception(self, context: CircuitBreaker, exc: BaseException):
        """Handle exception during the code block"""

    @abc.abstractmethod
    def handle_end_request(self, context: CircuitBreaker):
        """Handle proper execution after the code block"""


@dataclass
class ClosedState(State):
    """In closed state, track for failure."""

    failure_count: int
    name: str = "closed"

    def __init__(self) -> None:
        self.failure_count = 0

    def handle_new_request(self, context: CircuitBreaker):
        """When the circuit is closed, the new request has no incidence"""

    def handle_exception(self, context: CircuitBreaker, exc: BaseException):
        self.failure_count += 1
        if self.failure_count >= context.threshold:
            opened = OpenedState()
            context.set_state(opened)
        else:
            context.mark_failure(self.failure_count)

    def handle_end_request(self, context: CircuitBreaker):
        """Reset in case the request is ok"""
        if self.failure_count > 0:
            context.recover_failure()
        self.failure_count = 0


@dataclass
class OpenedState(State, Exception):
    """In open state, reopen after a TTL."""

    name: str = "opened"
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


@dataclass
class HalfOpenedState(State):
    """In half open state, decide to reopen or to close."""

    name: str = "half-opened"

    def handle_new_request(self, context: CircuitBreaker):
        """In half open state, we reset the failure counter to restart 0."""
        context.recover_failure()

    def handle_exception(self, context: CircuitBreaker, exc: BaseException):
        opened = OpenedState()
        context.set_state(opened)

    def handle_end_request(self, context: CircuitBreaker):
        context.set_state(ClosedState())
