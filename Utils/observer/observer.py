from typing import Callable, Sequence, Generator, Any

from .exceptions import BadArgument, EventNotFound


class EventContainer(list):
    # TODO: Every function must have the same arguments
    argument_mapping: Sequence[str]

    def __init__(self, *args):
        self.argument_mapping = []
        super().__init__(filter(self.validate_object, args))

    @staticmethod
    def get_arguments(func: Callable) -> tuple:
        return func.__code__.co_varnames

    @staticmethod
    def is_func(__object: Callable) -> bool:
        return callable(__object)

    @classmethod
    def has_valid_arguments(cls, func: Callable, argument_mapping: Sequence[str]) -> bool:
        return cls.get_arguments(func) == tuple(argument_mapping)

    def validate_object(self, __object: Callable):
        """Checks if the function conforms to the argument mapping and is also :class:`Callable`
        """
        arguments = self.get_arguments(__object)
        if not self.argument_mapping:
            self.argument_mapping = arguments

        if self.is_func(__object) is False:
            raise TypeError('Expected {0!r} for argument: `{1!r}` not {1.__class__!r}.'.format(Callable, __object))
        if self.has_valid_arguments(__object, self.argument_mapping) is False:
            raise BadArgument(f'Expected Arguments = {self.argument_mapping}, Received: {arguments} instead')

        return __object

    def append(self, __object: Callable) -> None:
        super().append(self.validate_object(__object))


class EventHandler:
    """
    Handles all the events that is registered to this handler

    Attributes
    ----------
    event_handlers: dict[:class:`str`, :class:`EventHandler`]
        A dictionary of Event Handlers

    """
    event_handlers = {}

    def __new__(cls, name: str):
        """

        Parameters
        ----------
        name: :class:`str`
            The name of the event handler

        """
        if not isinstance(name, str):
            raise TypeError('Expected {0!r} not {1.__class__!r}.'.format(str, name))

        if name not in cls.event_handlers:  # create a new class
            cls.event_handlers[name] = super().__new__(cls)
        return cls.event_handlers[name]

    events: dict[str, EventContainer]

    def __init__(self, name: str):
        self.events = {}

    def add_event(self, event_name: str, function: Callable):
        if event_name not in (events := self.events):  # wild
            events[event_name] = EventContainer()
        events[event_name].append(function)

    def remove_event(self, name: str):
        """Removes and Event

        Parameters
        ----------
        name: :class:`str`
            The name of the event to be removed

        """

    def start_event(self, event_name: str, args) -> Generator[Any, None, None]:
        """Starts an Event
        """
        if event_name not in (events := self.events):  # wild
            raise EventNotFound(event_name)
        else:
            for func in events[event_name]:
                if len(EventContainer.get_arguments(func)) == 0:
                    # if the function has no arguments
                    yield func()
                else:
                    yield func(args)

    def register_to_event(self, event_name: str):
        """decorator for adding events
        """

        def decorator(func):
            self.add_event(event_name, func)
            return func

        return decorator
