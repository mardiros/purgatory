"""
Circuit breaker state model.

The state model is implemented using the State pattern from the Gang Of Four.
"""
import abc
import time
from dataclasses import dataclass
from types import TracebackType
from typing import Callable, List, Optional, Tuple, Type, Union, cast

from purgatory.domain.messages.base import Event
from purgatory.domain.messages.events import (
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.typing import TTL, CircuitName, StateName, Threshold

ExcludeExcType = Type[BaseException]
ExcludeTypeFunc = Tuple[ExcludeExcType, Callable[..., bool]]
ExcludeType = List[
    Union[
        ExcludeExcType,
        ExcludeTypeFunc,
    ]
]

CLOSED: StateName = "closed"
OPENED: StateName = "opened"
HALF_OPENED: StateName = "half-opened"


class Context:
    name: CircuitName
    threshold: Threshold
    ttl: TTL
    messages: List[Event]
    exclude_list: ExcludeType

    def __init__(
        self,
        name: CircuitName,
        threshold: Threshold,
        ttl: TTL,
        state: StateName = "closed",
        failure_count: int = 0,
        opened_at: Optional[float] = None,
        exclude: ExcludeType = None,
    ) -> None:
        self.name = name
        self.ttl = ttl
        self.threshold = threshold

        args = {OpenedState.name: [name]}.get(state, [])
        self._state = {
            ClosedState.name: ClosedState,
            OpenedState.name: OpenedState,
            HalfOpenedState.name: HalfOpenedState,
        }[state](*args)
        self._state.opened_at = opened_at
        self._state.failure_count = failure_count
        self.messages = []
        self.exclude_list = exclude or []

    @property
    def state(self) -> StateName:
        return cast(StateName, self._state.name)

    @property
    def opened_at(self) -> Optional[float]:
        return self._state.opened_at

    @property
    def failure_count(self) -> Optional[int]:
        return self._state.failure_count

    def set_state(self, state: "State") -> None:
        self._state = state
        self.messages.append(
            ContextChanged(
                self.name,
                self.state,
                state.opened_at,
            )
        )

    def mark_failure(self, failure_count: int) -> None:
        self.messages.append(
            CircuitBreakerFailed(
                self.name,
                failure_count,
            )
        )

    def recover_failure(self) -> None:
        self.messages.append(
            CircuitBreakerRecovered(
                self.name,
            )
        )

    def handle_new_request(self) -> None:
        self._state.handle_new_request(self)

    def handle_exception(self, exc: BaseException) -> None:
        failed = True
        for exctype_func in self.exclude_list:

            if isinstance(exctype_func, tuple):
                exctype, func = cast(ExcludeTypeFunc, exctype_func)
            else:
                exctype, func = cast(ExcludeExcType, exctype_func), lambda exc: True

            if isinstance(exc, exctype):
                failed = not func(exc)
                break
        if failed:
            self._state.handle_exception(self, exc)
        else:
            self._state.handle_end_request(self)

    def handle_end_request(self) -> None:
        self._state.handle_end_request(self)

    def __enter__(self) -> "Context":
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
            f"<Context "
            f'name="{self.name}" '
            f'state="{self.state}" '
            f'threshold="{self.threshold}" ttl="{self.ttl}">'
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Context)
            and self.name == other.name
            and self.threshold == other.threshold
            and self.ttl == other.ttl
        )


class State(abc.ABC):
    failure_count: Optional[int] = None
    opened_at: Optional[float] = None
    name: str = ""

    @abc.abstractmethod
    def handle_new_request(self, context: Context) -> None:
        """Handle new code block"""

    @abc.abstractmethod
    def handle_exception(self, context: Context, exc: BaseException) -> None:
        """Handle exception during the code block"""

    @abc.abstractmethod
    def handle_end_request(self, context: Context) -> None:
        """Handle proper execution after the code block"""


@dataclass
class ClosedState(State):
    """In closed state, track for failure."""

    failure_count: int
    name: StateName = CLOSED

    def __init__(self) -> None:
        self.failure_count = 0

    def handle_new_request(self, context: Context) -> None:
        """When the circuit is closed, the new request has no incidence"""

    def handle_exception(self, context: Context, exc: BaseException) -> None:
        self.failure_count += 1
        context.mark_failure(self.failure_count)
        if self.failure_count >= context.threshold:
            opened = OpenedState(context.name)
            context.set_state(opened)

    def handle_end_request(self, context: Context) -> None:
        """Reset in case the request is ok"""
        if self.failure_count > 0:
            context.recover_failure()
        self.failure_count = 0


@dataclass
class OpenedState(State, Exception):
    """In open state, reopen after a TTL."""

    opened_at: float
    name: StateName = OPENED

    def __init__(self, circuit_name: CircuitName) -> None:
        Exception.__init__(self, f"Circuit {circuit_name} is open")
        self.opened_at = time.time()
        self.circuit_name = circuit_name

    def handle_new_request(self, context: Context) -> None:
        closed_at = self.opened_at + context.ttl
        if time.time() > closed_at:
            context.set_state(HalfOpenedState())
            return context.handle_new_request()
        raise self

    def handle_exception(self, context: Context, exc: BaseException) -> None:
        """
        When the circuit is opened, the OpenState is raised before entering.

        This function is never called.
        """

    def handle_end_request(self, context: Context) -> None:
        """
        When the circuit is opened, the OpenState is raised before entering.

        This function is never called.
        """


@dataclass
class HalfOpenedState(State):
    """In half open state, decide to reopen or to close."""

    name: StateName = HALF_OPENED

    def handle_new_request(self, context: Context) -> None:
        """In half open state, we reset the failure counter to restart 0."""

    def handle_exception(self, context: Context, exc: BaseException) -> None:
        """If an exception happens, then the circuit is reopen directly."""
        opened = OpenedState(context.name)
        context.set_state(opened)

    def handle_end_request(self, context: Context) -> None:
        """Otherwise, the circuit is closed, back to normal."""
        context.recover_failure()
        context.set_state(ClosedState())
