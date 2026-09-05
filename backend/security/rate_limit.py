import time

from backend.config import MAX_MESSAGES_PER_SECOND


class RateLimiter:
    def __init__(self, max_messages_per_second: int = MAX_MESSAGES_PER_SECOND):
        self.max_messages_per_second = max_messages_per_second
        self._history = {}

    def allow(self, key: str):
        now = time.time()
        bucket = self._history.setdefault(key, [])
        bucket[:] = [ts for ts in bucket if now - ts < 1.0]
        if len(bucket) >= self.max_messages_per_second:
            return False
        bucket.append(now)
        return True
