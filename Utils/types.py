from typing import Union, Optional, TypeVar

from scrapy import Selector
from scrapy.selector import SelectorList

__all__ = (
    'StringOrInt',
    'IdStringPair',
    'OptionalStr',
    'OptionalInt',
    'CORYN_NULL_TYPES',
    'SelectorType',
    'OptionalEmpty',
    'Empty'
)

CORYN_NULL_TYPES = {'Unknown', 'N/A', 'unknown'}
StringOrInt = Union[str, int]
IdStringPair = tuple[Optional[str], str]
StringStringPair = tuple[str, str]
OptionalStr = Optional[str]
OptionalInt = Optional[int]
SelectorType = Union[Selector, SelectorList]


class _Empty:
    """Custom Type for Empty Assignment"""
    def __bool__(self):
        return False

    def __repr__(self):
        return 'Empty'

    def __len__(self):
        return 0


Empty = _Empty()


T = TypeVar('T')
OptionalEmpty = Union[T, type(Empty)]
