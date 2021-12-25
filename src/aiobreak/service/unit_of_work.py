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

    def __enter__(self) -> AbstractUnitOfWork:
        return self

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


class _InMemoryUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.circuit_breakers = InMemoryRepository()

    def commit(self):
        pass

    def rollback(self):
        pass


class InMemoryUnitOfWork(AbstractUnitOfWork):
    instance = None

    def __init__(self):
        if self.instance is None:
            InMemoryUnitOfWork.instance = _InMemoryUnitOfWork()

    @property
    def circuit_breakers(self):
        return self.instance.circuit_breakers

    def __enter__(self) -> AbstractUnitOfWork:
        return self.instance.__enter__()

    def __exit__(self, *args):
        return self.instance.__exit__()

    def commit(self):
        return self.instance.commit()

    def rollback(self):
        return self.instance.rollback()
