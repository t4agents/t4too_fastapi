import time
from collections import OrderedDict
from typing import Any, Optional


class MemoryTTLCache:
    def __init__(self, max_size: int = 2048) -> None:
        self._max_size = max_size
        self._data: OrderedDict[str, tuple[Any, Optional[float]]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and expires_at <= time.time():
            self._data.pop(key, None)
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = (value, expires_at)
        self._evict()

    def _evict(self) -> None:
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._data.items() if exp is not None and exp <= now]
        for k in expired_keys:
            self._data.pop(k, None)

        while len(self._data) > self._max_size:
            self._data.popitem(last=False)


_CACHE = MemoryTTLCache(max_size=2048)


def cache_get(key: str) -> Any | None:
    return _CACHE.get(key)


def cache_set(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    _CACHE.set(key, value, ttl_seconds=ttl_seconds)
