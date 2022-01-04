from purgatory.domain.messages.commands import CreateCircuitBreaker
from purgatory.domain.messages.events import (
    CircuitBreakerCreated,
    CircuitBreakerFailed,
    CircuitBreakerRecovered,
    ContextChanged,
)
from purgatory.domain.model import Context
from purgatory.service._async.unit_of_work import AsyncAbstractUnitOfWork


async def register_circuit_breaker(
    cmd: CreateCircuitBreaker, uow: AsyncAbstractUnitOfWork
) -> Context:
    """
    Register circuit breaker in the repository

    when receiving the CreateCircuitBreaker command.
    """
    ret = Context(cmd.name, cmd.threshold, cmd.ttl)
    await uow.contexts.register(ret)
    uow.contexts.messages.append(
        CircuitBreakerCreated(cmd.name, cmd.threshold, cmd.ttl)
    )
    return ret


async def save_circuit_breaker_state(
    evt: ContextChanged, uow: AsyncAbstractUnitOfWork
) -> None:
    """
    Save the circuit breaker state in the repository

    when receiving the ContextChanged event.
    """
    await uow.contexts.update_state(evt.name, evt.state, evt.opened_at)


async def inc_circuit_breaker_failure(
    evt: CircuitBreakerFailed, uow: AsyncAbstractUnitOfWork
) -> None:
    """
    Increment the number of failure in the repository

    when receiving the CircuitBreakerFailed event.
    """
    await uow.contexts.inc_failures(evt.name, evt.failure_count)


async def reset_failure(
    evt: CircuitBreakerRecovered, uow: AsyncAbstractUnitOfWork
) -> None:
    """
    Reset the number of failure in the repository

    when receiving the CircuitBreakerRecovered event.
    """
    await uow.contexts.reset_failure(evt.name)
