import pytest

from purgatory import CircuitBreakerFactory
from purgatory.service.messagebus import MessageRegistry


@pytest.fixture()
def circuitbreaker():
    yield CircuitBreakerFactory()


@pytest.fixture()
def messagebus():
    yield MessageRegistry()
