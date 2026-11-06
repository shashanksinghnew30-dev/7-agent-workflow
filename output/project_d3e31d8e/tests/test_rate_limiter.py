import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
import time
from src.rate_limiter_core import TokenBucketRateLimiter

class TestRateLimiter(unittest.TestCase):
    def test_burst_and_refill(self):
        limiter = TokenBucketRateLimiter(rate_per_second=10.0, capacity=2.0)
        self.assertTrue(limiter.acquire(1.0))
        self.assertTrue(limiter.acquire(1.0))
        self.assertFalse(limiter.acquire(1.0))
        time.sleep(0.15)
        self.assertTrue(limiter.acquire(1.0))

if __name__ == "__main__":
    unittest.main()
