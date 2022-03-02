"""Contains all the exceptions for the observer module"""


class EventError(Exception):
    """Base Exception"""


class HandlerError(EventError):
    """Base Exception for Event Handlers"""


class HandlerNotFound(HandlerError):
    """Exception raised when an event handler is not found

    This inherits from :exc:`HandlerError`
    """
    def __init__(self, handler_name: str):
        super(HandlerNotFound, self).__init__(f'Handler named: `{handler_name}` could not be found.')


class EventNotFound(HandlerError):
    """Exception raised when an event handler cannot find an event

    This inherits from :exc:`HandlerError`
    """
    def __init__(self, event_name: str):
        super(EventNotFound, self).__init__(f'Event named: `{event_name}` could not be found.')


class EventContainerError(EventError):
    """Base Exception for Event Containers"""


class BadArgument(EventContainerError):
    """Exception raised when a parsing or conversion failure is encountered
    on an argument to pass into a command.

    This inherits from :exc:`EventContainerError`
    """
