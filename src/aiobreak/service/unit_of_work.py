"""Unit of work"""
from __future__ import annotations
import abc

from ..domain.repository import (
    AbstractRepository,
    InMemoryRepository
)


class AbstractUnitOfWork(abc.ABC):
    circuit_breakers: AbstractRepository

    def collect_new_events(self):
        while self.circuit_breakers.messages:
            yield self.circuit_breakers.messages.pop(0)

    async def __aenter__(self) -> AbstractUnitOfWork:
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    @abc.abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self):
        raise NotImplementedError


class InMemoryUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.circuit_breakers = InMemoryRepository()

    async def commit(self):
        pass

    async def rollback(self):
        pass
