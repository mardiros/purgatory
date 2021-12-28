import abc
from typing import List, Optional

from purgatory.domain.messages.base import Message
from purgatory.domain.model import CircuitBreaker
from purgatory.typing import CircuitBreakerName


class AbstractRepository(abc.ABC):

    messages: List[Message]

    @abc.abstractmethod
    async def get(self, name: CircuitBreakerName) -> Optional[CircuitBreaker]:
        """Load breakers from the repository."""

    @abc.abstractmethod
    async def register(self, model: CircuitBreaker):
        """Add a circuit breaker into the repository."""

    @abc.abstractmethod
    async def update_state(
        self,
        name: str,
        state: str,
        opened_at: Optional[float],
    ):
        """Sate the new staate of the circuit breaker into the repository."""


class InMemoryRepository(AbstractRepository):
    def __init__(self):
        self.breakers = {}
        self.messages = []

    async def get(self, name: CircuitBreakerName) -> Optional[CircuitBreaker]:
        """Add a circuit breaker into the repository."""
        return self.breakers.get(name)

    async def register(self, model: CircuitBreaker):
        """Add a circuit breaker into the repository."""
        self.breakers[model.name] = model

    async def update_state(
        self,
        name: str,
        state: str,
        opened_at: Optional[float],
    ):
        """Because the get method return the object directly, nothing to do here."""
