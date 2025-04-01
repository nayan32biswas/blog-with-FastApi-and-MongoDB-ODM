from collections.abc import Callable
from functools import wraps
from time import time
from typing import Any

Function = Callable[..., Any]


def timing(f: Function) -> Function:
    @wraps(f)
    def wrap(*args: list[Any], **kwargs: dict[Any, Any]) -> Any:
        ts = time()
        result = f(*args, **kwargs)
        print(f"func:{f.__name__} took: {round(time() - ts, 3)} sec")
        return result

    return wrap
