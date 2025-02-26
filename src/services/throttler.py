from config import openai_settings
import asyncio
from typing import List, Callable, TypeVar, Awaitable

T = TypeVar("T")  # Generic type variable

class ApiThrottler:
    """
    A class to throttle API requests in batches to prevent rate limiting.
    """

    @staticmethod
    async def throttle_requests(
        request_funcs: List[Callable[[], Awaitable[T]]],  # List of async functions returning type T
        batch_size: int = 10,
        delay: float = 1.05
    ) -> List[T]:  # Returns a list of results of type T
        """
        Executes a list of async callables in batches with a delay.

        :param request_funcs: A list of async callables (functions with no arguments)
        :param batch_size: Number of requests to run concurrently in a batch
        :param delay: Delay (in seconds) between batches
        :return: A list of results with the same type as the callable return type
        """
        results: List[T] = []
        for i in range(0, len(request_funcs), batch_size):
            batch = request_funcs[i:i + batch_size]
            results.extend(await asyncio.gather(*[func() for func in batch]))  # Execute batch
            if i + batch_size < len(request_funcs):
                await asyncio.sleep(delay)  # Wait before next batch

        return results

    @staticmethod
    async def throttle_openai_requests(request_funcs: List[Callable[[], Awaitable[T]]]) -> List[T]:
        rpm = openai_settings.requests_per_minute
         # Delay in seconds between requests
        batch_size = rpm // 60  # Number of requests per batch
        delay = 1   # Delay in seconds between batches

        """
        Executes a list of async callables in batches with a delay.

        :param request_funcs: A list of async callables (functions with no arguments)
        :param batch_size: Number of requests to run concurrently in a batch
        :param delay: Delay (in seconds) between batches
        :return: A list of results with the same type as the callable return type
        """
        results: List[T] = []
        for i in range(0, len(request_funcs), batch_size):
            batch = request_funcs[i:i + batch_size]
            results.extend(await asyncio.gather(*[func() for func in batch]))  # Execute batch
            if i + batch_size < len(request_funcs):
                await asyncio.sleep(delay)  # Wait before next batch

        return results
