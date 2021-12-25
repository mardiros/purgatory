import pytest

from purgatory import CircuitBreakerFactory
from purgatory.service.messagebus import MessageBus


@pytest.fixture()
def circuitbreaker():
    yield CircuitBreakerFactory()


@pytest.fixture()
def messagebus():
    yield MessageBus()
