"""
Standalone verification runner.
"""
from src.cache_core import ResilientLRUCache

def main():
    print("=== Initializing ResilientLRUCache ===")
    cache = ResilientLRUCache(capacity=3, default_ttl=5.0)
    
    print("[1] Inserting 3 items: alpha, beta, gamma...")
    cache.put("alpha", {"payload": "first"})
    cache.put("beta", {"payload": "second"})
    cache.put("gamma", {"payload": "third"})
    
    print("[2] Reading 'alpha' (refreshing LRU status)...")
    print(f"    Value: {cache.get('alpha')}")
    
    print("[3] Inserting 4th item: delta (triggers eviction of oldest 'beta')...")
    cache.put("delta", {"payload": "fourth"})
    
    print(f"    alpha present? {cache.contains('alpha')}")
    print(f"    beta present?  {cache.contains('beta')} (Expected: False - evicted)")
    print(f"    gamma present? {cache.contains('gamma')}")
    print(f"    delta present? {cache.contains('delta')}")
    
    print("[4] Cache Statistics Snapshot:")
    print(f"    {cache.stats.snapshot()}")
    print("=== Demo Completed Successfully ===")

if __name__ == "__main__":
    main()
