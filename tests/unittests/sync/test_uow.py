from purgatory.domain.messages.base import Message
from purgatory.sync.repository import SyncInMemoryRepository
from purgatory.sync.unit_of_work import SyncAbstractUnitOfWork, SyncInMemoryUnitOfWork


class SyncTrackableUnitOfWork(SyncAbstractUnitOfWork):
    def __init__(self) -> None:
        super().__init__()
        self.commited = False
        self.rollbacked = False
        self.contexts = SyncInMemoryRepository()

    def commit(self):
        self.commited = True

    def rollback(self):
        self.rollbacked = True


def test_commit_is_explicit():
    uow = SyncTrackableUnitOfWork()
    with uow:
        pass
    assert uow.commited is False
    assert uow.rollbacked is False


def test_rollack_is_implicit():
    uow = SyncTrackableUnitOfWork()
    try:
        with uow:
            raise RuntimeError("Boom")
    except RuntimeError:
        pass
    assert uow.commited is False
    assert uow.rollbacked is True


def test_uow_is_collecting_events():
    uow = SyncInMemoryUnitOfWork()
    a = Message()
    b = Message()
    c = Message()
    uow.contexts.messages = [a, b, c]
    events = list(uow.collect_new_events())
    assert events == [a, b, c]
