""" Global sessions

This module gathers all global-level caches and sessions except for database,
which live in baleine.db.

The shutdown function is called before the bot exits.
"""
import asyncio

_http_session = None

def http():
    """ Return an http session to use for http requests """
    global _http_session
    if _http_session is None:
        import aiohttp
        _http_session = aiohttp.ClientSession()
    return _http_session


async def http_shutdown():
    global _http_session
    if _http_session is not None:
        await _http_session.close()
        _http_session = None


async def shutdown():
    await http_shutdown()
    await asyncio.sleep(1)
