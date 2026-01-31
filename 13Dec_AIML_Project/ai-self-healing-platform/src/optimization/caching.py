"""
Caching Module - Redis-based Caching
Implements caching strategies for performance optimization
"""

import json
import logging
from typing import Any, Optional, Callable
from datetime import timedelta
from functools import wraps
import hashlib

# Redis client
try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not installed. Install with: pip install redis")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages Redis cache operations
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, default_ttl: int = 300):
        """
        Initialize cache manager
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            default_ttl: Default TTL in seconds
        """
        self.default_ttl = default_ttl
        self.enabled = REDIS_AVAILABLE
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis caching disabled - redis package not installed")
            self.client = None
            return
        
        try:
            self.client = Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test connection
            self.client.ping()
            logger.info(f"✓ Connected to Redis at {host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Cache will be disabled")
            self.client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        # Create a unique key based on function arguments
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache MISS: {key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            
            self.client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern
        
        Args:
            pattern: Pattern to match (e.g., "metrics:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching '{pattern}'")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def flush_all(self) -> bool:
        """Clear entire cache"""
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.flushdb()
            logger.warning("All cache cleared!")
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled or not self.client:
            return {"status": "disabled"}
        
        try:
            info = self.client.info()
            return {
                "status": "enabled",
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_keys": self.client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)


# Global cache instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
    
    return _cache_manager


def cached(ttl: int = 300, key_prefix: str = "cache"):
    """
    Decorator to cache function results
    
    Usage:
        @cached(ttl=600, key_prefix="metrics")
        def get_metrics(user_id: int):
            # expensive operation
            return data
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key
            cache_key = cache._generate_key(key_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(key_prefix: str):
    """
    Decorator to invalidate cache after function execution
    
    Usage:
        @cache_invalidate(key_prefix="metrics")
        def update_metrics(user_id: int, data):
            # update operation
            return success
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate cache
            cache = get_cache_manager()
            pattern = f"{key_prefix}:*"
            cache.clear_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator


class RateLimiter:
    """
    Simple rate limiter using Redis
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache = cache_manager or get_cache_manager()
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if request is allowed under rate limit
        
        Args:
            key: Unique identifier (e.g., user_id, ip_address)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if allowed, False if rate limit exceeded
        """
        if not self.cache.enabled:
            return True  # No rate limiting if cache disabled
        
        try:
            rate_key = f"rate_limit:{key}"
            current = self.cache.client.get(rate_key)
            
            if current is None:
                # First request in window
                self.cache.client.setex(rate_key, window_seconds, 1)
                return True
            
            current_count = int(current)
            
            if current_count >= max_requests:
                logger.warning(f"Rate limit exceeded for {key}")
                return False
            
            # Increment counter
            self.cache.client.incr(rate_key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error


# Example usage
if __name__ == '__main__':
    import time
    
    # Initialize cache
    cache = CacheManager(host="localhost", port=6379)
    
    # Test basic operations
    print("\n=== Testing Cache Operations ===")
    
    # Set
    cache.set("test_key", {"data": "test_value"}, ttl=60)
    
    # Get
    value = cache.get("test_key")
    print(f"Retrieved: {value}")
    
    # Test decorator
    @cached(ttl=30, key_prefix="expensive")
    def expensive_function(x: int, y: int):
        print(f"Computing {x} + {y}...")
        time.sleep(1)  # Simulate expensive operation
        return x + y
    
    print("\n=== Testing Cached Decorator ===")
    
    # First call - should compute
    result1 = expensive_function(5, 3)
    print(f"Result 1: {result1}")
    
    # Second call - should use cache
    result2 = expensive_function(5, 3)
    print(f"Result 2: {result2} (from cache)")
    
    # Different args - should compute
    result3 = expensive_function(10, 20)
    print(f"Result 3: {result3}")
    
    # Test rate limiting
    print("\n=== Testing Rate Limiter ===")
    
    limiter = RateLimiter(cache)
    
    for i in range(5):
        allowed = limiter.is_allowed("user_123", max_requests=3, window_seconds=60)
        print(f"Request {i+1}: {'✓ Allowed' if allowed else '✗ Blocked'}")
    
    # Get stats
    print("\n=== Cache Statistics ===")
    stats = cache.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Cleanup
    cache.delete("test_key")
    cache.clear_pattern("expensive:*")
    
    print("\n✓ Cache tests completed!")