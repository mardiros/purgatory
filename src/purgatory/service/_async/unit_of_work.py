"""Unit of work"""
from __future__ import annotations

import abc
from types import TracebackType
from typing import Generator, Optional, Type

from purgatory.domain.messages import Message
from purgatory.service._async.repository import (
    AsyncAbstractRepository,
    AsyncInMemoryRepository,
    AsyncRedisRepository,
)


class AsyncAbstractUnitOfWork(abc.ABC):
    contexts: AsyncAbstractRepository

    def collect_new_events(self) -> Generator[Message, None, None]:
        while self.contexts.messages:
            yield self.contexts.messages.pop(0)

    async def initialize(self) -> None:
        """Override to initialize  repositories."""

    async def __aenter__(self) -> AsyncAbstractUnitOfWork:
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
    async def commit(self) -> None:
        """Commit the transation."""

    @abc.abstractmethod
    async def rollback(self) -> None:
        """Rollback the transation."""


class AsyncInMemoryUnitOfWork(AsyncAbstractUnitOfWork):
    def __init__(self) -> None:
        self.contexts = AsyncInMemoryRepository()

    async def commit(self) -> None:
        """Do nothing."""

    async def rollback(self) -> None:
        """Do nothing."""


class AsyncRedisUnitOfWork(AsyncAbstractUnitOfWork):
    def __init__(self, url: str) -> None:
        self.contexts = AsyncRedisRepository(url)

    async def initialize(self) -> None:
        await self.contexts.initialize()

    async def commit(self) -> None:
        """Do nothing."""

    async def rollback(self) -> None:
        """Do nothing."""
