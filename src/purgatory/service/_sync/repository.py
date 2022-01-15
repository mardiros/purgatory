import abc
import json
from typing import List, Optional

from purgatory.domain.messages.base import Message
from purgatory.domain.model import Context
from purgatory.typing import CircuitName


class ConfigurationError(RuntimeError):
    pass


class SyncAbstractRepository(abc.ABC):

    messages: List[Message]

    def initialize(self):
        """Override to initialize the repository asynchronously"""

    @abc.abstractmethod
    def get(self, name: CircuitName) -> Optional[Context]:
        """Load breakers from the repository."""

    @abc.abstractmethod
    def register(self, context: Context):
        """Add a circuit breaker into the repository."""

    @abc.abstractmethod
    def update_state(
        self,
        name: str,
        state: str,
        opened_at: Optional[float],
    ):
        """Sate the new staate of the circuit breaker into the repository."""

    @abc.abstractmethod
    def inc_failures(self, name: str, failure_count: int):
        """Increment the number of failure in the repository."""

    @abc.abstractmethod
    def reset_failure(self, name: str):
        """Reset the number of failure in the repository."""


class SyncInMemoryRepository(SyncAbstractRepository):
    def __init__(self):
        self.breakers = {}
        self.messages = []

    def get(self, name: CircuitName) -> Optional[Context]:
        """Add a circuit breaker into the repository."""
        return self.breakers.get(name)

    def register(self, context: Context):
        """Add a circuit breaker into the repository."""
        self.breakers[context.name] = context

    def update_state(
        self,
        name: str,
        state: str,
        opened_at: Optional[float],
    ):
        """Because the get method return the object directly, nothing to do here."""

    def inc_failures(self, name: str, failure_count: int):
        """Because the get method return the object directly, nothing to do here."""

    def reset_failure(self, name: str):
        """Reset the number of failure in the repository."""


class SyncRedisRepository(SyncAbstractRepository):
    def __init__(self, url: str):
        try:
            import redis
        except ImportError:
            raise ConfigurationError("redis extra dependencies not installed.")
        self.redis = redis.from_url(url)
        self.messages = []
        self.prefix = "cbr::"

    def initialize(self):
        self.redis.initialize()

    def get(self, name: CircuitName) -> Optional[Context]:
        """Add a circuit breaker into the repository."""
        data = self.redis.get(f"{self.prefix}{name}")
        if not data:
            return None
        breaker = json.loads(data or "{}")
        failure_count = self.redis.get(f"{self.prefix}{name}::failure_count")
        if failure_count:
            breaker["failure_count"] = int(failure_count)
        cbreaker = Context(**breaker)
        return cbreaker

    def register(self, context: Context):
        """Add a circuit breaker into the repository."""
        data = json.dumps(
            {
                "name": context.name,
                "threshold": context.threshold,
                "ttl": context.ttl,
                "state": context.state,
                "opened_at": context.opened_at,
            }
        )
        self.redis.set(f"{self.prefix}{context.name}", data)

    def update_state(
        self,
        name: str,
        state: str,
        opened_at: Optional[float],
    ):
        """Store the new state in the repository."""
        data = self.redis.get(f"{self.prefix}{name}")
        breaker = json.loads(data or "{}")
        breaker["state"] = state
        breaker["opened_at"] = opened_at
        self.redis.set(f"{self.prefix}{name}", json.dumps(breaker))

    def inc_failures(self, name: str, failure_count: int):
        """Store the new state in the repository."""
        self.redis.incr(f"{self.prefix}{name}::failure_count")

    def reset_failure(self, name: str):
        """Reset the number of failure in the repository."""
        self.redis.set(f"{self.prefix}{name}::failure_count", "0")
