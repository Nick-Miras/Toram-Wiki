from typing import Callable, Optional


def get_exception_from(func: Callable, args) -> Optional[Exception]:
    try:
        func(*args)
    except Exception as exc:
        return exc
    else:
        return
