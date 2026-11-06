"""
Thread-Safe Token Bucket Rate Limiter with Burst Support.
"""
import time
import threading

class TokenBucketRateLimiter:
    def __init__(self, rate_per_second: float, capacity: float):
        if rate_per_second <= 0 or capacity <= 0:
            raise ValueError("Rate and capacity must be positive")
        self.rate = rate_per_second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = threading.Lock()

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

    def acquire(self, tokens: float = 1.0) -> bool:
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
