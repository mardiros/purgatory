"""Unit of work"""
from __future__ import annotations

import abc
from types import TracebackType
from typing import Optional, Type

from purgatory.domain.repository import (
    AbstractRepository,
    InMemoryRepository,
    RedisRepository,
)


class AbstractUnitOfWork(abc.ABC):
    circuit_breakers: AbstractRepository

    def collect_new_events(self):
        while self.circuit_breakers.messages:
            yield self.circuit_breakers.messages.pop(0)

    async def initialize(self):
        """Override to initialize  repositories."""

    async def __aenter__(self) -> AbstractUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        """Rollback in case of exception."""
        if exc:
            await self.rollback()

    @abc.abstractmethod
    async def commit(self):
        """Commit the transation."""

    @abc.abstractmethod
    async def rollback(self):
        """Rollback the transation."""


class InMemoryUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.circuit_breakers = InMemoryRepository()

    async def commit(self):
        """Do nothing."""

    async def rollback(self):
        """Do nothing."""


class RedisUnitOfWork(AbstractUnitOfWork):
    def __init__(self, url: str):
        self.circuit_breakers = RedisRepository(url)

    async def initialize(self):
        await self.circuit_breakers.initialize()

    async def commit(self):
        """Do nothing."""

    async def rollback(self):
        """Do nothing."""
