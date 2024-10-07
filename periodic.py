import asyncio


async def periodic(interval_sec, coro_name, *args, **kwargs):
    while True:
        await asyncio.sleep(interval_sec)
        await coro_name(*args, **kwargs)
