"""Contains all the exceptions for the paginator"""
from uuid import UUID


class PaginatorException(Exception):
    """The base exception"""


class InitializationError(PaginatorException):
    """Exception raised when a class should be/not initialized.

    This inherits from :exc:`PaginatorException`
    """


class ChildNotFound(PaginatorException):
    """Exception raised when a PageDataNode child is not found"""

    def __init__(self, find: UUID | str):
        super().__init__(f'Cannot find child: {find}')


class CurrentNodeNotFound(PaginatorException):
    """Exception raised when current node of :class:`PageTreeController` cannot be found"""

    def __init__(self):
        super().__init__('Current node of PageTreeController cannot be found')


class PageDataException(PaginatorException):
    pass


class DisplayDataNotFound(PageDataException):

    def __init__(self):
        super().__init__('Display Data Not Found')
