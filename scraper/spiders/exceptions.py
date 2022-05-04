from typing import Type


class ScraperException(Exception):
    """Base Exception class for :module: scraper"""


class BadArgument(ScraperException):
    pass


class InitializationError(ScraperException):
    def __init__(self, cls: Type, error: str):
        super().__init__(f'{cls}: {error}')


class InvalidUrl(ScraperException):
    def __init__(self, url: str):
        super().__init__(f'Invalid Url: {url}')
