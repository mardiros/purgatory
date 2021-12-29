import abc
import json
from typing import List, Optional

from purgatory.domain.messages.base import Message
from purgatory.domain.model import CircuitBreaker
from purgatory.typing import CircuitBreakerName


class ConfigurationError(RuntimeError):
    pass


class AbstractRepository(abc.ABC):

    messages: List[Message]

    async def initialize(self):
        """Override to initialize the repository asynchronously"""

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

    async def inc_failures(self, name: str, failure_count: int):
        """Increment the number of failure in the repository."""


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

    async def inc_failures(self, name: str, failure_count: int):
        """Because the get method return the object directly, nothing to do here."""


class RedisRepository(AbstractRepository):
    def __init__(self, url: str):
        try:
            import aioredis
        except ImportError:
            raise ConfigurationError("redis extra dependencies not installed.")
        self.redis = aioredis.from_url(url)
        self.messages = []
        self.prefix = "cbr::"

    async def initialize(self):
        await self.redis.initialize()

    async def get(self, name: CircuitBreakerName) -> Optional[CircuitBreaker]:
        """Add a circuit breaker into the repository."""
        data = await self.redis.get(f"{self.prefix}{name}")
        if not data:
            return None
        breaker = json.loads(data)
        failure_count = await self.redis.get(f"{self.prefix}{name}::failure_count")
        if failure_count:
            breaker["failure_count"] = int(failure_count)
        cbreaker = CircuitBreaker(**breaker)
        return cbreaker

    async def register(self, model: CircuitBreaker):
        """Add a circuit breaker into the repository."""
        data = json.dumps(
            {
                "name": model.name,
                "threshold": model.threshold,
                "ttl": model.ttl,
                "state": model.state,
                "opened_at": model.opened_at,
            }
        )
        await self.redis.set(f"{self.prefix}{model.name}", data)

    async def update_state(
        self,
        name: str,
        state: str,
        opened_at: Optional[float],
    ):
        """Store the new state in the repository."""
        data = await self.redis.get(f"{self.prefix}{name}")
        breaker = json.loads(data)
        breaker["state"] = state
        breaker["opened_at"] = opened_at
        await self.redis.set(f"{self.prefix}{name}", json.dumps(breaker))

    async def inc_failures(self, name: str, failure_count: int):
        """Store the new state in the repository."""
        await self.redis.incr(f"{self.prefix}{name}::failure_count")
