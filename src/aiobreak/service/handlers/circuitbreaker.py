from aiobreak.domain.messages.commands import CreateCircuitBreaker
from aiobreak.domain.model import CircuitBreaker
from aiobreak.service.unit_of_work import AbstractUnitOfWork


async def register_circuit_breaker(cmd: CreateCircuitBreaker, uow: AbstractUnitOfWork):
    await uow.circuit_breakers.register(
        CircuitBreaker(cmd.name, cmd.threshold, cmd.ttl)
    )
