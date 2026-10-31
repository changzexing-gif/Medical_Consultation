from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Generic, TypeVar


T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: int = 600, max_size: int = 512):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._data: OrderedDict[str, tuple[float, T]] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> T | None:
        now = time.monotonic()
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            created, value = item
            if now - created > self.ttl:
                self._data.pop(key, None)
                return None
            self._data.move_to_end(key)
            return value

    def set(self, key: str, value: T) -> None:
        with self._lock:
            self._data[key] = (time.monotonic(), value)
            self._data.move_to_end(key)
            while len(self._data) > self.max_size:
                self._data.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
