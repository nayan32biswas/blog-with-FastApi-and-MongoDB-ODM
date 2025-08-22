from collections.abc import Callable
from functools import wraps
from time import time
from typing import Any

Function = Callable[..., Any]


def timing(func: Function) -> Function:
    @wraps(func)
    def wrap(*args: list[Any], **kwargs: dict[Any, Any]) -> Any:
        ts = time()
        result = func(*args, **kwargs)
        print(f"func:{func.__name__} took: {round(time() - ts, 3)} sec")
        return result

    return wrap


def async_timing(func: Function) -> Function:
    @wraps(func)
    async def wrap(*args: list[Any], **kwargs: dict[Any, Any]) -> Any:
        ts = time()
        result = await func(*args, **kwargs)
        print(f"func:{func.__name__} took: {round(time() - ts, 3)} sec")
        return result

    return wrap


def async_lru_cache(maxsize: int = 128) -> Callable[[Function], Function]:
    cache: dict[Any, Any] = {}
    order: list[Any] = []

    def decorator(func: Function) -> Function:
        @wraps(func)
        async def wrapper(*args: list[Any], **kwargs: dict[Any, Any]) -> Any:
            key = str((args, frozenset(kwargs.items())))
            if key in cache:
                order.remove(key)
                order.append(key)
                return cache[key]

            result = await func(*args, **kwargs)
            cache[key] = result
            order.append(key)

            if len(cache) > maxsize:
                oldest_key = order.pop(0)
                cache.pop(oldest_key)

            return result

        return wrapper

    return decorator
