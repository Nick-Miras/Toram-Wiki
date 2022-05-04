"""Xpath Helper Functions"""
from scrapy import Selector


def normalize_space(string: str) -> str:
    """Xpath Normalize Space"""
    return f'normalize-space({string})'


def substring_before(string: str, divider: str) -> str:
    return f'substring-before({string}, "{divider}")'


def substring_after(string: str, divider: str) -> str:
    return f'substring-after({string}, "{divider}")'


def get_non_empty_string(xpath: str) -> str:
    """
    xpath for extracting text from a selector that return multiple text results
    """
    return normalize_space(f'{xpath}[string-length({normalize_space(".")})>1]')


def extract_string_from_node(container: Selector) -> str:
    return container.xpath(normalize_space('.')).get()
