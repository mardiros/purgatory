"""Unit of work"""
from __future__ import annotations

import abc
from types import TracebackType
from typing import Generator, Optional, Type

from purgatory.domain.messages import Message
from purgatory.service.repository import (
    AbstractRepository,
    InMemoryRepository,
    RedisRepository,
)


class AbstractUnitOfWork(abc.ABC):
    contexts: AbstractRepository

    def collect_new_events(self) -> Generator[Message, None, None]:
        while self.contexts.messages:
            yield self.contexts.messages.pop(0)

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
        self.contexts = InMemoryRepository()

    async def commit(self):
        """Do nothing."""

    async def rollback(self):
        """Do nothing."""


class RedisUnitOfWork(AbstractUnitOfWork):
    def __init__(self, url: str):
        self.contexts = RedisRepository(url)

    async def initialize(self):
        await self.contexts.initialize()

    async def commit(self):
        """Do nothing."""

    async def rollback(self):
        """Do nothing."""
