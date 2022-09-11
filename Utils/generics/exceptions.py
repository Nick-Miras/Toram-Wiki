import inspect
from typing import Callable, Optional


def get_exception_from(func: Callable, args) -> Optional[Exception]:
    try:
        func(*args)
    except Exception as exc:
        return exc
    else:
        return


def is_generator(func) -> bool:
    """check if a function is a generator"""
    return inspect.isgeneratorfunction(func)
