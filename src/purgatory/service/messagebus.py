"""
Propagate commands and events to every registered handles.

"""
import logging
from collections import defaultdict
from typing import Any, Callable

from purgatory.domain.messages.base import Command, Event, Message

from . import unit_of_work

log = logging.getLogger(__name__)


class ConfigurationError(RuntimeError):
    """Prevents bad usage of the add_listener."""


class MessageRegistry(object):
    """Store all the handlers for commands an events."""

    def __init__(self):
        self.commands_registry = {}
        self.events_registry = defaultdict(list)

    def add_listener(self, msg_type: type, callback: Callable):
        if issubclass(msg_type, Command):
            if msg_type in self.commands_registry:
                raise ConfigurationError(
                    f"{msg_type} command has been registered twice"
                )
            self.commands_registry[msg_type] = callback
        elif issubclass(msg_type, Event):
            self.events_registry[msg_type].append(callback)
        else:
            raise ConfigurationError(
                f"Invalid usage of the listen decorator: "
                f"type {msg_type} should be a command or an event"
            )

    def remove_listener(self, msg_type: type, callback: Callable):
        if issubclass(msg_type, Command):
            if msg_type not in self.commands_registry:
                raise ConfigurationError(f"{msg_type} command has not been registered")
            del self.commands_registry[msg_type]
        elif issubclass(msg_type, Event):
            try:
                self.events_registry[msg_type].remove(callback)
            except ValueError:
                raise ConfigurationError(f"{msg_type} event has not been registered")
        else:
            raise ConfigurationError(
                f"Invalid usage of the listen decorator: "
                f"type {msg_type} should be a command or an event"
            )

    async def handle(
        self, message: Message, uow: unit_of_work.AbstractUnitOfWork
    ) -> Any:
        """
        Notify listener of that event registered with `messagebus.add_listener`.
        Return the first event from the command.
        """
        queue = [message]
        ret = None
        while queue:
            message = queue.pop(0)
            if not isinstance(message, (Command, Event)):
                raise RuntimeError(f"{message} was not an Event or Command")
            msg_type = type(message)
            if msg_type in self.commands_registry:
                cmdret = await self.commands_registry[msg_type](message, uow)
                if ret is None:
                    ret = cmdret
                queue.extend(uow.collect_new_events())
            elif msg_type in self.events_registry:
                for callback in self.events_registry[msg_type]:
                    await callback(message, uow)
                    queue.extend(uow.collect_new_events())
        return ret
