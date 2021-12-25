from purgatory.domain.messages.commands import CreateCircuitBreaker
from purgatory.domain.model import CircuitBreaker
from purgatory.service.unit_of_work import AbstractUnitOfWork


async def register_circuit_breaker(cmd: CreateCircuitBreaker, uow: AbstractUnitOfWork) -> CircuitBreaker:
    ret = CircuitBreaker(cmd.name, cmd.threshold, cmd.ttl)
    await uow.circuit_breakers.register(ret
        
    )

    return ret