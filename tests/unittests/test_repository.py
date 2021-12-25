import pytest

from aiobreak.domain.repository import InMemoryRepository
from aiobreak.domain.model import CircuitBreaker


@pytest.mark.asyncio
async def test_timeslot_in_memory_repository():
    repo = InMemoryRepository()
    cbreaker = CircuitBreaker("dummy", 5, 30.0)
    await repo.register(cbreaker)
    assert repo.breakers == {"dummy": cbreaker}
