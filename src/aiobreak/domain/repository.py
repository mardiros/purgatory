import abc
from typing import Dict, List


from .model import CircuitBreaker
from ..domain.messages.base import Message
from ..typing import CircuitBreakerName


class AbstractRepository(abc.ABC):

    messages: List[Message]
    breakers = Dict[CircuitBreakerName, CircuitBreaker]

    @abc.abstractmethod
    async def load(self):
        """Load breakers from the repository."""

    @abc.abstractmethod
    async def register(self, model: CircuitBreaker):
        """Add a circuit breaker into the repository."""


class InMemoryRepository(AbstractRepository):

    def __init__(self):
        self.breakers = {}

    async def load(self):
        pass

    async def register(self, model: CircuitBreaker):
        """Add a circuit breaker into the repository."""
        self.breakers[model.name] = model
