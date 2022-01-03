import pytest

from purgatory.domain.messages.base import Message
from purgatory.service._async.repository import AsyncInMemoryRepository
from purgatory.service._async.unit_of_work import AsyncAbstractUnitOfWork, AsyncInMemoryUnitOfWork


class TrackableUnitOfWork(AsyncAbstractUnitOfWork):
    def __init__(self) -> None:
        super().__init__()
        self.commited = False
        self.rollbacked = False
        self.contexts = AsyncInMemoryRepository()

    async def commit(self):
        self.commited = True

    async def rollback(self):
        self.rollbacked = True


@pytest.mark.asyncio
async def test_commit_is_explicit():
    uow = TrackableUnitOfWork()
    async with uow:
        pass
    assert uow.commited is False
    assert uow.rollbacked is False


@pytest.mark.asyncio
async def test_rollack_is_implicit():
    uow = TrackableUnitOfWork()
    try:
        async with uow:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert uow.commited is False
    assert uow.rollbacked is True


@pytest.mark.asyncio
async def test_uow_is_collecting_events():
    uow = AsyncInMemoryUnitOfWork()
    a = Message()
    b = Message()
    c = Message()
    uow.contexts.messages = [a, b, c]
    events = list(uow.collect_new_events())
    assert events == [a, b, c]
