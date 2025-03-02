import asyncio
import functools
import threading
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar, cast

T = TypeVar("T")


def set_timeout(time_limit: int):
    """
    Decorator to add a time limit to synchronous and asynchronous methods
    For asynchronous methods, use asyncio.wait_for to set the timeout
    For synchronous methods, use threading.Thread to set the timeout

    Args:
        time_limit: Time limit in seconds
    """

    def decorator(
        func: Callable[..., T] | Callable[..., Coroutine[None, None, T]],
    ) -> Callable[..., T] | Callable[..., Coroutine[None, None, T]]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def wrapper_async(*args, **kwargs) -> T:
                try:
                    return await asyncio.wait_for(
                        cast(Callable[..., Coroutine[None, None, T]], func)(*args, **kwargs), timeout=time_limit
                    )
                except TimeoutError:
                    raise TimeoutError(f"Async method exceeded time limit of {time_limit} seconds")

            return wrapper_async
        else:

            @functools.wraps(func)
            def wrapper_sync(*args, **kwargs) -> T:
                result: list[Any] = [None]
                exception: list[Exception | None] = [None]

                def target():
                    try:
                        result[0] = cast(Callable[..., T], func)(*args, **kwargs)
                    except Exception as e:
                        exception[0] = e

                thread = threading.Thread(target=target)
                thread.start()
                thread.join(time_limit)

                if thread.is_alive():
                    thread.daemon = True  # Allow the thread to be terminated when the main thread exits
                    raise TimeoutError(f"Sync method exceeded time limit of {time_limit} seconds")

                if exception[0]:
                    raise exception[0]

                return result[0]

            return wrapper_sync

    return decorator
