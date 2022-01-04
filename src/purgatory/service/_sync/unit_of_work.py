"""Unit of work"""
from __future__ import annotations

import abc
from types import TracebackType
from typing import Generator, Optional, Type

from purgatory.domain.messages import Message
from purgatory.service._sync.repository import (
    SyncAbstractRepository,
    SyncInMemoryRepository,
    SyncRedisRepository,
)


class SyncAbstractUnitOfWork(abc.ABC):
    contexts: SyncAbstractRepository

    def collect_new_events(self) -> Generator[Message, None, None]:
        while self.contexts.messages:
            yield self.contexts.messages.pop(0)

    def initialize(self):
        """Override to initialize  repositories."""

    def __enter__(self) -> SyncAbstractUnitOfWork:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        """Rollback in case of exception."""
        if exc:
            self.rollback()

    @abc.abstractmethod
    def commit(self):
        """Commit the transation."""

    @abc.abstractmethod
    def rollback(self):
        """Rollback the transation."""


class SyncInMemoryUnitOfWork(SyncAbstractUnitOfWork):
    def __init__(self):
        self.contexts = SyncInMemoryRepository()

    def commit(self):
        """Do nothing."""

    def rollback(self):
        """Do nothing."""


class SyncRedisUnitOfWork(SyncAbstractUnitOfWork):
    def __init__(self, url: str):
        self.contexts = SyncRedisRepository(url)

    def initialize(self):
        self.contexts.initialize()

    def commit(self):
        """Do nothing."""

    def rollback(self):
        """Do nothing."""
