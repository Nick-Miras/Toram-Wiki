"""Contains all the exceptions for the paginator"""
from ctypes import Union
from uuid import UUID


class PaginatorException(Exception):
    """The base exception"""


class InitializationError(PaginatorException):
    """Exception raised when a class should be/not initialized.

    This inherits from :exc:`PaginatorException`
    """


class ChildNotFound(PaginatorException):
    """Exception raised when a Page Date child is not found"""

    def __init__(self, find: Union[UUID, str]):
        super().__init__(f'Cannot find child: {find}')
