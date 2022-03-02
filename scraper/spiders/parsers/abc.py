"""
using the composite design pattern
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Generator, Optional, TypeVar, Generic, Type, Any, TypedDict, Final, final

import scrapy
from pydantic.generics import GenericModel as PydanticGenericModel
from scrapy import Selector

from Utils.types import SelectorType
from Utils.generics import arrays
from .container_paths import ContainerPaths
from ..exceptions import BadArgument, InitializationError

ResultType = TypeVar('ResultType')


class ParserType(Enum):
    Composite = auto()
    Leaf = auto()


class ParserInformation(TypedDict):
    name: str
    type: ParserType


def parser_information_builder(parser: ParserLeaf) -> ParserInformation:
    return {'name': parser.name, 'type': parser.type}


class ParserResults(PydanticGenericModel, Generic[ResultType]):
    parser: ParserInformation
    result: Optional[ResultType]


class ParserResultWrapper(scrapy.Item):
    results: list[ParserResults] = scrapy.Field()


def parser_results_builder(cls: ParserLeaf, result: Any, type_var):
    return ParserResults[type_var](parser=parser_information_builder(cls), result=result)


def return_parser_results(type_var):
    """A decorator for the :`ParserResults`: builder
    """

    def function(func):
        def arguments(cls, container: SelectorType) -> list[ParserResults]:
            result = func(cls, container)
            return [parser_results_builder(cls, result=result, type_var=type_var)]
        return arguments
    return function


class BaseParser(ABC):
    type: ParserType
    container_path: Type[ContainerPaths]

    def __new__(cls, *args, **kwargs):
        if getattr(cls, 'container_path', None) is None:
            raise InitializationError(cls, 'attribute: container_path cannot be found')
        if getattr(cls, 'type', None) is None:
            raise InitializationError(cls, 'attribute: type cannot be found')
        return super().__new__(cls)

    def __init__(self, response: Selector, container_path: Type[ContainerPaths]):
        self.response = response
        self.container_path = container_path

    @final
    def parse(self) -> Generator[ParserResultWrapper, None, None]:
        """The method that returns the values to the client"""
        containers = self.response.xpath(self.container_path.get())
        for container in containers:
            if container:
                yield ParserResultWrapper(results=self.get_result(container))

    @classmethod
    @abstractmethod  # protected method (if this was not python)
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        """The method that is used by the parse method to get results from the container object"""


class CompositeParser(BaseParser, ABC):
    type: Final = ParserType.Composite
    parsers: list[Type[ParserLeaf]] = []

    @classmethod
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        def generate() -> Generator[ParserResults, None, None]:
            for parser in cls.parsers:
                yield parser.get_result(container)
        return array.flatten(list(generate()))

    @classmethod
    def add_parser(cls, parser: Type[ParserLeaf]):  # override if possible
        cond, return_string = cls.parser_validator(parser)
        if cond is False:
            raise BadArgument(return_string)

        cls.parsers.append(parser)

    @classmethod
    def remove_parser(cls, name: str):
        for parser in cls.parsers:
            if parser.name == name:
                cls.parsers.remove(parser)

    @classmethod
    def clear_parsers(cls):
        cls.parsers.clear()

    @classmethod
    def get_class(cls):
        return cls.__class__

    @staticmethod
    @abstractmethod
    def parser_validator(parser: Type[ParserLeaf]) -> tuple[bool, Optional[str]]:
        """
        Returns
        -------
        boolean and error string
        """


class ParserLeaf(BaseParser, ABC):  # template design pattern
    name: str
    type: Final = ParserType.Leaf

    def __new__(cls, *args, **kwargs):
        if getattr(cls, 'name', None) is None:
            raise InitializationError(cls, 'attribute: name cannot be found')
        return super().__new__(cls)
