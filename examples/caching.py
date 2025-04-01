"""
Caching utilities for Hammx

This module demonstrates how to add caching functionality
to Hammx clients without modifying the core implementation.
"""
import time
import asyncio
import json
import hashlib
from functools import wraps
from hammx import Hammx


async def with_memory_cache(client, ttl=60):
    """Add in-memory caching to GET requests.
    
    This middleware caches successful GET responses for the specified TTL.
    Only 200 responses are cached.
    
    Args:
        client: A Hammx client instance
        ttl: Cache TTL in seconds (default: 60)
        
    Example:
        client = Hammx('https://api.example.com')
        cached_client = await with_memory_cache(client, ttl=300)  # 5 minute cache
    """
    # Use a dict as a simple cache
    cache = {}
    original_get = client.GET
    
    @wraps(original_get)
    async def cached_get(*args, **kwargs):
        # Create a cache key based on URL and query params
        url = client._url(*args)
        params = kwargs.get('params', {})
        cache_key = f"{url}:{json.dumps(params, sort_keys=True)}"
        
        # Hash the key if it's too long
        if len(cache_key) > 100:
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Check if we have a valid cached response
        now = time.time()
        if cache_key in cache and now - cache[cache_key]['time'] < ttl:
            print(f"Cache hit: {url}")
            return cache[cache_key]['response']
            
        # Make the actual request
        print(f"Cache miss: {url}")
        response = await original_get(*args, **kwargs)
        
        # Cache successful responses
        if response.status_code == 200:
            # Store a copy of the response
            cache[cache_key] = {
                'response': response,
                'time': now
            }
            
        return response
        
    # Replace the GET method
    client.GET = cached_get
    return client


class DiskCache:
    """A simple disk-based cache implementation.
    
    This is a simplified example - a production version would need:
    - Better file handling and concurrency control
    - Cache size limits and LRU eviction
    - More sophisticated serialization
    """
    def __init__(self, cache_dir='.cache', ttl=3600):
        import os
        self.cache_dir = cache_dir
        self.ttl = ttl
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def get(self, key):
        """Get a value from the cache."""
        import os
        import pickle
        
        path = os.path.join(self.cache_dir, key)
        if not os.path.exists(path):
            return None
            
        # Check TTL
        now = time.time()
        if now - os.path.getmtime(path) > self.ttl:
            os.remove(path)
            return None
            
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None
    
    def set(self, key, value):
        """Set a value in the cache."""
        import os
        import pickle
        
        path = os.path.join(self.cache_dir, key)
        try:
            with open(path, 'wb') as f:
                pickle.dump(value, f)
        except Exception:
            # Silently fail on cache errors
            pass


async def with_disk_cache(client, cache_dir='.cache', ttl=3600):
    """Add disk-based caching to GET requests.
    
    This middleware caches successful GET responses to disk for the specified TTL.
    
    Note: This is a simplified example - in production you might want to:
    - Use a more sophisticated cache implementation
    - Add cache eviction policies
    - Handle concurrent access better
    
    Args:
        client: A Hammx client instance
        cache_dir: Directory to store cache files (default: .cache)
        ttl: Cache TTL in seconds (default: 3600 - 1 hour)
        
    Example:
        client = Hammx('https://api.example.com')
        cached_client = await with_disk_cache(client)
    """
    import hashlib
    
    # Create a cache instance
    cache = DiskCache(cache_dir, ttl)
    original_get = client.GET
    
    @wraps(original_get)
    async def cached_get(*args, **kwargs):
        # Create a cache key based on URL and query params
        url = client._url(*args)
        params = kwargs.get('params', {})
        cache_key = f"{url}:{json.dumps(params, sort_keys=True)}"
        
        # Hash the key to create a valid filename
        cache_key = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Check if we have a valid cached response
        cached_response = cache.get(cache_key)
        if cached_response:
            print(f"Disk cache hit: {url}")
            return cached_response
            
        # Make the actual request
        print(f"Disk cache miss: {url}")
        response = await original_get(*args, **kwargs)
        
        # Cache successful responses
        if response.status_code == 200:
            cache.set(cache_key, response)
            
        return response
        
    # Replace the GET method
    client.GET = cached_get
    return client


# Demonstrate caching middleware
async def demo():
    # Create a client with memory cache
    client = Hammx('https://httpbin.org')
    cached_client = await with_memory_cache(client, ttl=10)
    
    try:
        # First request - cache miss
        print("\nFirst request:")
        await cached_client.get.GET()
        
        # Second request - should hit cache
        print("\nSecond request (should be cached):")
        await cached_client.get.GET()
        
        # Wait for cache to expire
        print("\nWaiting for cache to expire...")
        await asyncio.sleep(11)
        
        # Third request - cache should be expired
        print("\nThird request (cache expired):")
        await cached_client.get.GET()
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(demo())
