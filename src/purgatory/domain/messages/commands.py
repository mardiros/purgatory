from dataclasses import dataclass

from purgatory.typing import TTL, Threshold

from .base import Command


@dataclass(frozen=True)
class CreateCircuitBreaker(Command):
    name: str
    threshold: Threshold
    ttl: TTL
