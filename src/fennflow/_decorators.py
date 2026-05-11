import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeAlias

CatchType: TypeAlias = type[Exception] | tuple[type[Exception], ...]


def reraise_with(
    exception: Exception,
    catch: CatchType = Exception,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except catch as e:
                raise exception from e

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except catch as e:
                raise exception from e

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
