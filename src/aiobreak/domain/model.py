"""
Circuit breaker state model.

The state model is implemented using the State pattern from the Gang Of Four.
"""
import abc
import time


class Context:
    def __init__(self, threshold: int, ttl: float) -> None:
        self.ttl = ttl
        self.threshold = threshold
        self._state = ClosedState()

    @property
    def name(self):
        return self._state.__class__.__name__

    def set_state(self, state: "State"):
        self._state = state

    async def handle_new_request(self):
        await self._state.handle_new_request(self)

    async def handle_exception(self, exc: BaseException):
        await self._state.handle_exception(self, exc)

    async def handle_end_request(self):
        await self._state.handle_end_request(self)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Context)
            and self.threshold == other.threshold
            and self.ttl == other.ttl
        )


class State(abc.ABC):

    @abc.abstractmethod
    async def handle_new_request(self, context: Context):
        """Handle new code block"""

    @abc.abstractmethod
    async def handle_exception(self, context: Context, exc: BaseException):
        """Handle exception during the code block"""

    @abc.abstractmethod
    async def handle_end_request(self, context: Context):
        """Handle proper execution after the code block"""

    def __eq__(self, other: object) -> bool:
        return self.__class__ == other.__class__


class ClosedState(State):
    """In closed state, track for failure."""

    def __init__(self) -> None:
        self.failure_count = 0

    async def handle_new_request(self, context: Context):
        """When the circuit is closed, the new request has no incidence"""

    async def handle_exception(self, context: Context, exc: BaseException):
        self.failure_count += 1
        if self.failure_count >= context.threshold:
            opened = OpenedState()
            context.set_state(opened)

    async def handle_end_request(self, context: Context):
        """Reset in case the request is ok"""
        self.failure_count = 0


class OpenedState(State, Exception):
    """In open state, reopen after a TTL."""

    def __init__(self) -> None:
        Exception.__init__(self, "Circuit breaker is open")
        self.opened_at = time.time()

    async def handle_new_request(self, context: Context):
        closed_at = self.opened_at + context.ttl
        if time.time() > closed_at:
            context.set_state(HalfOpenedState())
            return context.handle_new_request()
        raise self

    async def handle_exception(self, exc: BaseException):
        """
        When the circuit is opened, the OpenState is raised before entering.

        this function is never called.
        """

    async def handle_end_request(self):
        """
        When the circuit is opened, the OpenState is raised before entering.

        this function is never called.
        """


class HalfOpenedState(State):
    """In half open state, decide to reopen or to close."""

    async def handle_new_request(self, context: Context):
        """In half open state, we check the result of the code block execution."""

    async def handle_exception(self, context: Context, exc: BaseException):
        opened = OpenedState()
        context.set_state(opened)

    async def handle_end_request(self, context: Context):
        context.set_state(ClosedState())
