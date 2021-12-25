"""
Propagate commands and events to every registered handles.

This module must be used as a singleton.

Use `messagebus.add_listener` to register a handler.

Use `messagebus.remove_listener` to unregister a handler

Use `messagebus.handle` to propagate an event or a command.

"""
import logging
from collections import defaultdict
from typing import Callable

from ..domain.messages.base import Message, Command, Event

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
                raise ConfigurationError("%s command has been registered twice")
            self.commands_registry[msg_type] = callback
        elif issubclass(msg_type, Event):
            self.events_registry[msg_type].append(callback)
        else:
            raise ConfigurationError(
                "Invalid usage of the listen decorator: "
                "type %s should be a command or an event"
            )

    def remove_listener(self, msg_type: type, callback: Callable):
        if issubclass(msg_type, Command):
            if msg_type not in self.commands_registry:
                raise ConfigurationError("%s command has not been registered")
            del self.commands_registry[msg_type]
        elif issubclass(msg_type, Event):
            try:
                self.events_registry[msg_type].remove(callback)
            except ValueError:
                log.error(f"Removing an unregistered callback {callback} has no effect")
        else:
            raise ConfigurationError(
                "Invalid usage of the listen decorator: "
                "type %s should be a command or an event"
            )

    def handle(self, message, uow: unit_of_work.AbstractUnitOfWork):
        """
        Notify listener of that event registered with `messagebus.add_listener`.
        """
        queue = [message]
        while queue:
            message = queue.pop(0)
            if not isinstance(message, (Command, Event)):
                raise RuntimeError(f"{message} was not an Event or Command")
            msg_type = type(message)
            if msg_type in self.commands_registry:
                self.commands_registry[msg_type](message, uow)
                queue.extend(uow.collect_new_events())
            elif msg_type in self.events_registry:
                for callback in self.events_registry[msg_type]:
                    callback(message, uow)
                    queue.extend(uow.collect_new_events())


_registry = MessageRegistry()


def add_listener(msg_type: type, callback: Callable):
    _registry.add_listener(msg_type, callback)


def remove_listener(msg_type: type, callback: Callable):
    _registry.remove_listener(msg_type, callback)


def handle(message: Message, uow: unit_of_work.AbstractUnitOfWork):
    """Handle a new message."""
    with uow:
        _registry.handle(message, uow)
        uow.commit()
