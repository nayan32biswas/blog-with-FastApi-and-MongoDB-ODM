from functools import wraps
from time import time
from typing import Any, Callable, Dict, List

Function = Callable[..., Any]


def timing(f: Function) -> Function:
    @wraps(f)
    def wrap(*args: List[Any], **kwargs: Dict[Any, Any]) -> Any:
        ts = time()
        result = f(*args, **kwargs)
        print(f"func:{f.__name__} took: {round(time() - ts, 3)} sec")
        return result

    return wrap
