from dataclasses import dataclass

from .base import Command


@dataclass(frozen=True)
class CreateCircuitBreaker(Command):
    name: str
    threshold: int
    ttl: float
