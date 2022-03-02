from typing import Optional

from scrapy import Selector

from Utils.types import CORYN_NULL_TYPES, SelectorType


def selector_from(container, xpath: str) -> SelectorType:
    """A wrapper shortcut for response and xpath
    """
    return container.xpath(xpath)


def is_container_null(container, xpath: str) -> tuple[bool, Optional[SelectorType]]:
    if (not_empty_container := selector_from(container, xpath)).get() in [None, *CORYN_NULL_TYPES]:
        return True, None
    return False, not_empty_container


def get_container_from(xpath: str):
    def inner(func):
        def wrapper(container: Selector):
            cond, container = is_container_null(container, xpath)
            if cond is True:
                return
            return func(container)
        return wrapper
    return inner
