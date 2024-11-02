"""
Propagate commands and events to every registered handles.

"""

import logging
from collections import defaultdict
from typing import Any, TypeVar, cast

from purgatory.domain.messages.base import Command, Event, Message

from ..typing import AsyncCommandHandler, AsyncEventHandler, AsyncMessageHandler
from .unit_of_work import AsyncAbstractUnitOfWork

log = logging.getLogger(__name__)

TCommand = TypeVar("TCommand", bound=Command)
TEvent = TypeVar("TEvent", bound=Event)


class ConfigurationError(RuntimeError):
    """Prevents bad usage of the add_listener."""


class AsyncMessageRegistry:
    """Store all the handlers for commands an events."""

    def __init__(self) -> None:
        self.commands_registry: dict[type[Command], AsyncCommandHandler[Command]] = {}
        self.events_registry: dict[type[Event], list[AsyncEventHandler[Event]]] = (
            defaultdict(list)
        )

    def add_listener(
        self, msg_type: type[Message], callback: AsyncMessageHandler[Any, Any]
    ) -> None:
        if issubclass(msg_type, Command):
            if msg_type in self.commands_registry:
                raise ConfigurationError(
                    f"{msg_type} command has been registered twice"
                )
            self.commands_registry[msg_type] = cast(
                AsyncCommandHandler[Command], callback
            )
        elif issubclass(msg_type, Event):
            self.events_registry[msg_type].append(
                cast(AsyncEventHandler[Event], callback)
            )
        else:
            raise ConfigurationError(
                f"Invalid usage of the listen decorator: "
                f"type {msg_type} should be a command or an event"
            )

    def remove_listener(
        self, msg_type: type, callback: AsyncMessageHandler[Any, Any]
    ) -> None:
        if issubclass(msg_type, Command):
            if msg_type not in self.commands_registry:
                raise ConfigurationError(f"{msg_type} command has not been registered")
            del self.commands_registry[msg_type]
        elif issubclass(msg_type, Event):
            try:
                self.events_registry[msg_type].remove(
                    cast(AsyncEventHandler[Event], callback)
                )
            except ValueError as exc:
                raise ConfigurationError(
                    f"{msg_type} event has not been registered"
                ) from exc
        else:
            raise ConfigurationError(
                f"Invalid usage of the listen decorator: "
                f"type {msg_type} should be a command or an event"
            )

    async def handle(self, message: Message, uow: AsyncAbstractUnitOfWork) -> Any:
        """
        Notify listener of that event registered with `messagebus.add_listener`.
        Return the first event from the command.
        """
        queue = [message]
        idx = 0
        ret = None
        while queue:
            message = queue.pop(0)
            if not isinstance(message, (Command, Event)):
                raise RuntimeError(f"{message} was not an Event or Command")
            msg_type = type(message)
            if msg_type in self.commands_registry:
                cmdret = await self.commands_registry[cast(type[Command], msg_type)](
                    cast(Command, message), uow
                )
                if idx == 0:
                    ret = cmdret
                queue.extend(uow.collect_new_events())
            elif msg_type in self.events_registry:
                for callback in self.events_registry[cast(type[Event], msg_type)]:
                    await callback(cast(Event, message), uow)
                    queue.extend(uow.collect_new_events())
            idx += 1
        return ret
