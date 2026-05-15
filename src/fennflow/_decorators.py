import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeAlias

CatchType: TypeAlias = (
    type[Exception] | tuple[type[Exception], ...] | Callable[[Exception], bool]
)


def reraise_with(
    exception: Exception,
    catch: CatchType = Exception,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:

        def _reraise_exception_if_match(e: Exception) -> None:
            if isinstance(catch, (type, tuple)):
                if isinstance(e, catch):
                    raise exception from e

            elif catch(e):
                raise exception from e

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                _reraise_exception_if_match(e)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _reraise_exception_if_match(e)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
