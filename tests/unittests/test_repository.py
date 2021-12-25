import pytest

from purgatory.domain.model import CircuitBreaker
from purgatory.domain.repository import InMemoryRepository


@pytest.mark.asyncio
async def test_timeslot_in_memory_repository():
    repo = InMemoryRepository()
    cbreaker = CircuitBreaker("dummy", 5, 30.0)
    await repo.register(cbreaker)
    assert repo.breakers == {"dummy": cbreaker}
