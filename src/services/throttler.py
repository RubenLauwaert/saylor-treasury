import asyncio
from typing import List, Callable, Any
from config import openai_settings

class ApiThrottler:

    @staticmethod
    async def throttle_edgar_requests(requests: List[Callable[[], Any]]) -> List[Any]:
        batch_size = 10  # Number of requests per batch
        delay = 1  # Delay in seconds between batches
        results = []

        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            results.extend(await asyncio.gather(*[req() for req in batch]))
            if i + batch_size < len(requests):
                await asyncio.sleep(delay)  # Wait for 1 second between batches

        return results

    @staticmethod
    async def throttle_openai_requests(requests: List[Callable[[], Any]]) -> List[Any]:
        rpm = openai_settings.requests_per_minute
        delay = 60 / rpm  # Delay in seconds between requests
        results = []

        for req in requests:
            results.append(await req())
            await asyncio.sleep(delay)  # Wait for the calculated delay between requests

        return results
