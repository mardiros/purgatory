import abc
import json
from typing import Any, Optional

from purgatory.domain.messages.base import Message
from purgatory.domain.model import Context
from purgatory.service._redis import SyncRedis
from purgatory.typing import CircuitName


class ConfigurationError(RuntimeError):
    pass


class SyncAbstractRepository(abc.ABC):
    messages: list[Message]

    def initialize(self) -> None:  # noqa B027
        """Override to initialize the repository asynchronously"""

    @abc.abstractmethod
    def get(self, name: CircuitName) -> Optional[Context]:
        """Load breakers from the repository."""

    @abc.abstractmethod
    def register(self, context: Context) -> None:
        """Add a circuit breaker into the repository."""

    @abc.abstractmethod
    def update_state(
        self,
        name: str,
        state: str,
        opened_at: Optional[float],
    ) -> None:
        """Sate the new staate of the circuit breaker into the repository."""

    @abc.abstractmethod
    def inc_failures(self, name: str, failure_count: int) -> None:
        """Increment the number of failure in the repository."""

    @abc.abstractmethod
    def reset_failure(self, name: str) -> None:
        """Reset the number of failure in the repository."""


class SyncInMemoryRepository(SyncAbstractRepository):
    def __init__(self) -> None:
        self.breakers: dict[CircuitName, Context] = {}
        self.messages: list[Message] = []

    def get(self, name: CircuitName) -> Optional[Context]:
        """Add a circuit breaker into the repository."""
        return self.breakers.get(name)

    def register(self, context: Context) -> None:
        """Add a circuit breaker into the repository."""
        self.breakers[context.name] = context

    def update_state(
        self,
        name: str,
        state: str,
        opened_at: Optional[float],
    ) -> None:
        """Because the get method return the object directly, nothing to do here."""

    def inc_failures(self, name: str, failure_count: int) -> None:
        """Because the get method return the object directly, nothing to do here."""

    def reset_failure(self, name: str) -> None:
        """Reset the number of failure in the repository."""


class SyncRedisRepository(SyncAbstractRepository):
    def __init__(self, url: str) -> None:
        try:
            from redis import asyncio as aioredis
        except ImportError as exc:
            raise ConfigurationError(  # coverage: ignore
                "redis extra dependencies not installed."
            ) from exc
        self.redis: SyncRedis = aioredis.from_url(url)  # type: ignore
        self.messages = []
        self.prefix = "cbr::"

    def initialize(self) -> None:
        self.redis.initialize()  # type: ignore

    def get(self, name: CircuitName) -> Optional[Context]:
        """Add a circuit breaker into the repository."""
        data: Any = self.redis.get(f"{self.prefix}{name}")
        if not data:
            return None
        breaker = json.loads(data or "{}")
        failure_count: int = self.redis.get(f"{self.prefix}{name}::failure_count") or 0
        if failure_count:
            breaker["failure_count"] = int(failure_count)
        cbreaker = Context(**breaker)
        return cbreaker

    def register(self, context: Context) -> None:
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
    ) -> None:
        """Store the new state in the repository."""
        data: str = self.redis.get(f"{self.prefix}{name}") or "{}"
        breaker = json.loads(data)
        breaker["state"] = state
        breaker["opened_at"] = opened_at
        self.redis.set(f"{self.prefix}{name}", json.dumps(breaker))

    def inc_failures(self, name: str, failure_count: int) -> None:
        """Store the new state in the repository."""
        self.redis.incr(f"{self.prefix}{name}::failure_count")

    def reset_failure(self, name: str) -> None:
        """Reset the number of failure in the repository."""
        self.redis.set(f"{self.prefix}{name}::failure_count", "0")
