import abc
from typing import Dict, List, Optional

from ..domain.messages.base import Message
from ..typing import CircuitBreakerName
from .model import CircuitBreaker


class AbstractRepository(abc.ABC):

    messages: List[Message]

    @abc.abstractmethod
    async def get(self, name: CircuitBreakerName) -> Optional[CircuitBreaker]:
        """Load breakers from the repository."""

    @abc.abstractmethod
    async def register(self, model: CircuitBreaker):
        """Add a circuit breaker into the repository."""


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
