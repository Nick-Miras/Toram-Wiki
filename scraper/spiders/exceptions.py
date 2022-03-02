from typing import Type


class ScraperException(Exception):
    """Base Exception class for :module: scraper"""


class BadArgument(ScraperException):
    ...


class InitializationError(ScraperException):
    def __init__(self, cls: Type, error: str):
        super().__init__(f'{cls}: {error}')
