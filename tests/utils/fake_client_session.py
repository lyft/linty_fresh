import copy
import asyncio
from typing import Dict, Tuple

from aiohttp.client import _RequestContextManager
from mock import call


class FakeClientResponse(object):
    def __init__(self, content, headers=None, status=201):
        self.headers = headers or {}
        self.status = status
        self.content = FakeStreamReader(content)

    @asyncio.coroutine
    def text(self):
        return self.content.content

    def __await__(self):
        yield
        return self

    @asyncio.coroutine
    def __aenter__(self):
        return self

    @asyncio.coroutine
    def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def close(self):
        pass

    def release(self):
        yield
        pass


class FakeClientSession(object):
    def __init__(self,
                 headers: Dict[str, str]=None,
                 url_map: Dict[Tuple[str, str], FakeClientResponse]=None,
                 *args, **kwargs):
        self.headers = headers
        self.url_map = url_map
        self.calls = []

    def __enter__(self):
        return self

    def __await__(self):
        yield
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @asyncio.coroutine
    def _get_stored_value(self, url, method):
        if (url, method) not in self.url_map:
            raise Exception('Invalid test request: ({}, {})'.format(
                url, method
            ))
        return self.url_map.get((url, method))

    def get(self, url, *args, **kwargs):
        updated_kwargs = self._update_headers(kwargs)
        self.calls.append(call.get(url, *args, **updated_kwargs))
        return _RequestContextManager(self._get_stored_value(url, 'get'))

    def post(self, url, *args, **kwargs):
        updated_kwargs = self._update_headers(kwargs)
        self.calls.append(call.post(url, *args, **updated_kwargs))
        return _RequestContextManager(self._get_stored_value(url, 'post'))

    def _update_headers(self, kwargs):
        result = copy.copy(kwargs)
        merged_headers = copy.copy(self.headers) if self.headers else {}
        if 'headers' in kwargs:
            merged_headers.update(kwargs['headers'])
            result['headers'] = merged_headers
        elif merged_headers:
            result['headers'] = merged_headers
        return result


class FakeStreamReader(object):
    def __init__(self, content: str):
        self.content = content
        self.lines = content.splitlines()
        self.line_index = 0

    @asyncio.coroutine
    def __aiter__(self):
        self.line_index = 0
        return self

    @asyncio.coroutine
    def __anext__(self):
        if self.line_index < len(self.lines):
            self.line_index += 1
            return self.lines[self.line_index - 1].encode()
        else:
            raise StopAsyncIteration
