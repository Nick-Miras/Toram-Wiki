from collections import Counter
from typing import Optional


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

def flatten(lst: list) -> list:
    return [item for sublist in lst for item in sublist]
