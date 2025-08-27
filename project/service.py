import asyncio
from typing import Any
from collections.abc import Callable


async def sync_for_async(fn: Callable[[Any], Any], *args, **kwargs):
    """
    This is analog for the django's sync_to_async function.
    :param fn: this is your sync function
    :param args: data in list of format
    :param kwargs: data in dict of format
    :return: result of your sync function
    """
    return await asyncio.to_thread(fn, *args, **kwargs)
