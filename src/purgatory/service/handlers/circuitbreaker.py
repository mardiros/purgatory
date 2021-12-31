from purgatory.domain.messages.commands import CreateCircuitBreaker
from purgatory.domain.messages.events import (
    CircuitBreakerCreated,
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.domain.model import Context
from purgatory.service.unit_of_work import AbstractUnitOfWork


async def register_circuit_breaker(
    cmd: CreateCircuitBreaker, uow: AbstractUnitOfWork
) -> Context:
    ret = Context(cmd.name, cmd.threshold, cmd.ttl)
    await uow.circuit_breakers.register(ret)
    uow.circuit_breakers.messages.append(
        CircuitBreakerCreated(cmd.name, cmd.threshold, cmd.ttl)
    )
    return ret


async def save_circuit_breaker_state(
    evt: ContextChanged, uow: AbstractUnitOfWork
) -> None:
    await uow.circuit_breakers.update_state(evt.name, evt.state, evt.opened_at)


async def inc_circuit_breaker_failure(
    evt: CircuitBreakerFailed, uow: AbstractUnitOfWork
) -> None:
    await uow.circuit_breakers.inc_failures(evt.name, evt.failure_count)


async def reset_failure(evt: CircuitBreakerRecovered, uow: AbstractUnitOfWork) -> None:
    await uow.circuit_breakers.reset_failure(evt.name)
