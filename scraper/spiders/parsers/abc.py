"""
using the composite design pattern
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generator, Optional, Type, Any, Final, final, Union

from scrapy.http import Response

from Utils.dataclasses.abc import WikiBaseModel
from Utils.generics import arrays
from Utils.types import SelectorType
from scraper.spiders.converters import IDataclassFactory
from scraper.spiders.exceptions import BadArgument, InitializationError
from scraper.spiders.parsers.container_paths import ContainerPaths
from scraper.spiders.parsers.models import ParserType, ParserInformation, ParserResults


def parser_information_builder(parser: ParserLeaf) -> ParserInformation:
    return {'name': parser.name, 'type': parser.type}


def parser_results_builder(cls: ParserLeaf, result: Any, type_var):
    return ParserResults[type_var](parser=parser_information_builder(cls), result=result)


def return_parser_results(type_var):
    """A decorator for the :`ParserResults`: builder
    """

    def function(func):
        def arguments(cls, container: SelectorType, response: Response) -> list[ParserResults]:
            result = func(cls, container, response)
            return [parser_results_builder(cls, result=result, type_var=type_var)]

        return arguments
    return function


class BaseParser(ABC):
    type: ParserType
    container_path: Type[ContainerPaths]

    def __new__(cls, *args, **kwargs):
        if getattr(cls, 'container_path', None) is None:
            raise InitializationError(cls, 'attribute: `container_path` cannot be found')
        if getattr(cls, 'type', None) is None:
            raise InitializationError(cls, 'attribute: `type` cannot be found')
        return super().__new__(cls)

    def __init__(self, container_path: Type[ContainerPaths], converter: Optional[IDataclassFactory] = None):
        self.container_path = container_path
        self.converter = converter

    @final
    def parse(self, response) -> Generator[Union[list[ParserResults], WikiBaseModel], None, None]:
        """The method that returns the results to the client"""
        containers = response.xpath(self.container_path.get())
        for container in containers:
            if container:
                if self.converter is None:
                    yield self.get_result(container, response)  # type: list[ParserResults]
                else:
                    yield self.converter.convert(self.get_result(container, response))  # type: WikiBaseModel

    @classmethod
    @abstractmethod  # protected method (if this was not python)
    def get_result(cls, container: SelectorType, response: Response) -> list[ParserResults]:
        """The method that is used by the parse method to get results from the container object
        """


class CompositeParser(BaseParser, ABC):
    type: Final = ParserType.Composite
    parsers: list[Type[ParserLeaf]] = []
    parser_leaf_class: Type[ParserLeaf]

    @classmethod
    def get_result(cls, container: SelectorType, response: Response) -> list[ParserResults]:
        def generate() -> Generator[ParserResults, None, None]:
            for parser in cls.parsers:
                yield parser.get_result(container, response)

        return arrays.flatten(list(generate()))

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

    @classmethod
    @final
    def parser_validator(cls, parser: Type[ParserLeaf]) -> tuple[bool, Optional[str]]:
        expected_parser = cls.parser_leaf_class
        if isinstance(parser, expected_parser) is False:
            return False, f'Expected {expected_parser} not {parser.__class__}'
        return True, None


class ParserLeaf(BaseParser, ABC):  # template design pattern
    name: str
    type: Final = ParserType.Leaf

    def __new__(cls, *args, **kwargs):
        if getattr(cls, 'name', None) is None:
            raise InitializationError(cls, 'attribute: name cannot be found')
        return super().__new__(cls)
