from typing import Union
import re


def try_int(num: str) -> Union[str, int]:
    """tries to convert to integer if fails then returns string
    """
    try:
        ret_val = int(num)
    except ValueError:
        return num
    else:
        return ret_val


def get_integer_from(string: str) -> int:
    return int(re.sub(r'\D', '', string))


def get_float_from(string: str) -> float:
    return float(re.sub(r'[^\d|.]', '', string))


def to_ordinal(number: int) -> str:
    return "%d%s" % (number, "tsnrhtdd"[(number // 10 % 10 != 1) * (number % 10 < 4) * number % 10::4])
