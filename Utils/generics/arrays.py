from collections import Counter
from typing import Optional, Iterable, TypeVar, Callable, Generator

T = TypeVar('T')

def has_duplicates(array: list) -> tuple[bool, Optional[list]]:
    """
    Returns
    -------
    tuple[`bool`, Optional[`list`]
        If whether there are duplicates or not
    """
    if duplicates := [pair for pair in Counter(array).most_common() if pair[1] > 1]:
        return True, duplicates
    return False, None


def flatten(lst: Iterable) -> list:
    return [item for sublist in lst for item in sublist]


def split_by_chunk(lst: list, chunk: int) -> list[list]:
    return [lst[i:i + chunk] for i in range(0, len(lst), chunk)]


def split_by_condition(lst: list[T], condition: Callable[[T], bool]) -> list[list[T]]:
    def get_chunks() -> Generator[list[T], None, None]:
        old_index = 0
        for index, item in enumerate(lst):
            if condition(item) is True:
                yield lst[old_index:index]
                old_index = index
        yield lst[old_index:len(lst)]

    return list(get_chunks())


def remove_duplicates(array: Iterable) -> list:
    return [element for element, count in Counter(array).items()]


def split_by_max_character_limit(lst: list[str]) -> list[list[str]]:
    current_string_length: int = 0

    def chunking_condition(string: str) -> bool:
        nonlocal current_string_length
        current_string_length += len(string)
        if current_string_length >= 1024:
            current_string_length = len(string)
            return True
        return False
    return split_by_condition(lst, chunking_condition)


def get_index_from_chunked_list(lst: list[list[T]], item: T) -> int:
    for index, element in enumerate(lst):
        if item in element:
            return index
    raise IndexError
