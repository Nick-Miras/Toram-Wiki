import hashlib
import re
from typing import Union, Type, Optional, TypeVar


def seperate_integer(num: int) -> str:
    """Examples: 100000 -> 100,000"""
    return f'{num:,}'


def try_int(num: str) -> Union[str, int]:
    """tries to convert to integer if fails then returns string
    """
    try:
        ret_val = int(num)
    except ValueError:
        return num
    else:
        return ret_val


def extract_integer_from(string: str) -> int:
    """Extracts Integer from String"""
    return int(re.sub(r'\D', '', string))


def get_float_from(string: str) -> float:
    return float(re.sub(r'[^\d|.]', '', string))


def to_ordinal(number: int) -> str:
    return "%d%s" % (number, "tsnrhtdd"[(number // 10 % 10 != 1) * (number % 10 < 4) * number % 10::4])


T = TypeVar('T')


def convert_to_type_if_not_none(obj: T, object_type: Type, /) -> Optional[T]:
    return object_type(obj) if obj is not None else None


def hash_int_using_sha256(num: int) -> str:
    return hashlib.sha256(str(num).encode()).hexdigest()
