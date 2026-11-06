from src.rate_limiter_core import TokenBucketRateLimiter
limiter = TokenBucketRateLimiter(5.0, 5.0)
print("Acquire tokens:", [limiter.acquire(1.0) for _ in range(6)])
