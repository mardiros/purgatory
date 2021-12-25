import pytest
from purgatory import CircuitBreakerFactory
from purgatory.domain.repository import InMemoryRepository
from purgatory.service.messagebus import MessageBus

@pytest.fixture()
def messagebus():
    yield MessageBus()
