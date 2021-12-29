import json
from typing import Any, Optional, cast

import pytest

from purgatory import CircuitBreakerFactory
from purgatory.domain.repository import RedisRepository
from purgatory.service.messagebus import MessageRegistry
from purgatory.service.unit_of_work import RedisUnitOfWork


@pytest.fixture()
def circuitbreaker():
    yield CircuitBreakerFactory()


@pytest.fixture()
def messagebus():
    yield MessageRegistry()


class FakeRedis:
    def __init__(self):
        self.initialized = False
        self.storage = None

    @property
    def deserialized_storage(self):
        return {
            key: json.loads(val) if isinstance(val, str) else val
            for key, val in self.storage.items()
        }

    async def initialize(self):
        self.initialized = True
        self.storage = {}

    async def get(self, key) -> Optional[Any]:
        if not self.initialized:
            raise RuntimeError("Unititialized")
        return self.storage.get(key)

    async def set(self, key, val):
        if not self.initialized:
            raise RuntimeError("Unititialized")
        self.storage[key] = val

    async def incr(self, key):
        if not self.initialized:
            raise RuntimeError("Unititialized")
        val = self.storage.get(key, 0) + 1
        self.storage[key] = val


@pytest.fixture()
def fake_redis():
    yield FakeRedis()


@pytest.fixture()
def redis_repository(fake_redis):
    repo = RedisRepository("redis://localhost")
    repo.redis = fake_redis
    yield repo


@pytest.fixture()
def redis_uow(fake_redis):
    repo = RedisUnitOfWork("redis://localhost")
    cast(RedisRepository, repo.circuit_breakers).redis = fake_redis
    yield repo


@pytest.fixture()
def circuitbreaker_redis(redis_uow):
    yield CircuitBreakerFactory(uow=redis_uow)
