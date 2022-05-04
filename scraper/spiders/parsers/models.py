from __future__ import annotations

from enum import Enum, auto
from typing import TypeVar, TypedDict, Generic, Optional

import scrapy
from pydantic import BaseModel as PydanticBaseModel
from pydantic.generics import GenericModel as PydanticGenericModel

ResultType = TypeVar('ResultType')


class ParserType(Enum):
    Composite = auto()
    Leaf = auto()


class ParserInformation(TypedDict):
    name: str
    type: ParserType


class ParserResults(PydanticGenericModel, Generic[ResultType]):
    parser: ParserInformation
    result: Optional[ResultType]


class ParserResultWrapper(scrapy.Item):
    result: list[ParserResults] = scrapy.Field()


class PydanticResultWrapper(scrapy.Item):
    result: PydanticBaseModel = scrapy.Field()
