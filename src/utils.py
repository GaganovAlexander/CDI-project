import asyncio


def make_async(func):
    async def inner(*args):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, func, *args)
        return result
    return inner
