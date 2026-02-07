"""
Optimization Module - Caching Layer with Redis Support
Provides caching functionality with automatic fallback to in-memory cache
"""

import logging
from typing import Any, Optional, Dict, List
from datetime import timedelta
import json
from functools import wraps
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    """
    Unified cache manager with Redis and in-memory fallback
    """
    
    def __init__(self, redis_client=None, default_ttl: int = 300):
        """
        Initialize cache manager
        
        Args:
            redis_client: Redis client instance (optional)
            default_ttl: Default time-to-live in seconds
        """
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.enabled = redis_client is not None
        
        # In-memory fallback
        self._memory_cache: Dict[str, tuple] = {}  # {key: (value, expiry_timestamp)}
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
        logger.info(f"CacheManager initialized (Redis: {self.enabled}, TTL: {default_ttl}s)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value is not None:
                    self.stats['hits'] += 1
                    try:
                        return json.loads(value)
                    except:
                        return value
                self.stats['misses'] += 1
                return None
            else:
                # In-memory cache
                if key in self._memory_cache:
                    value, expiry = self._memory_cache[key]
                    if time.time() < expiry:
                        self.stats['hits'] += 1
                        return value
                    else:
                        # Expired
                        del self._memory_cache[key]
                
                self.stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            
            if self.redis_client:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                self.redis_client.setex(key, ttl, value)
            else:
                # In-memory cache
                expiry = time.time() + ttl
                self._memory_cache[key] = (value, expiry)
            
            self.stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                if key in self._memory_cache:
                    del self._memory_cache[key]
            
            self.stats['deletes'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                if key in self._memory_cache:
                    _, expiry = self._memory_cache[key]
                    if time.time() < expiry:
                        return True
                    else:
                        del self._memory_cache[key]
                return False
                
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache"""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self._memory_cache.clear()
            
            logger.info("Cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            if self.redis_client:
                return [k.decode() if isinstance(k, bytes) else k 
                       for k in self.redis_client.keys(pattern)]
            else:
                # Simple pattern matching for in-memory
                if pattern == "*":
                    return list(self._memory_cache.keys())
                else:
                    # Basic wildcard support
                    import fnmatch
                    return [k for k in self._memory_cache.keys() 
                           if fnmatch.fnmatch(k, pattern)]
                    
        except Exception as e:
            logger.error(f"Cache keys error: {e}")
            return []
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            keys = self.keys(pattern)
            count = 0
            
            for key in keys:
                if self.delete(key):
                    count += 1
            
            logger.info(f"Deleted {count} keys matching '{pattern}'")
            return count
            
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            'enabled': self.enabled,
            'backend': 'redis' if self.redis_client else 'in-memory',
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }
        
        # Add Redis-specific stats
        if self.redis_client:
            try:
                info = self.redis_client.info('stats')
                stats['redis_stats'] = {
                    'total_connections_received': info.get('total_connections_received', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
            except:
                pass
        else:
            stats['in_memory_keys'] = len(self._memory_cache)
        
        return stats
    
    def cleanup_expired(self):
        """Clean up expired keys (for in-memory cache)"""
        if not self.redis_client:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._memory_cache.items()
                if current_time >= expiry
            ]
            
            for key in expired_keys:
                del self._memory_cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired keys")


class MetricsCache:
    """
    Specialized cache for metrics data with predefined TTLs
    """
    
    def __init__(self, cache_manager: CacheManager):
        """
        Initialize metrics cache
        
        Args:
            cache_manager: CacheManager instance
        """
        self.cache = cache_manager
        
        # Define TTLs for different metric types
        self.ttls = {
            'system_status': 5,      # 5 seconds
            'metrics': 60,           # 1 minute
            'anomalies': 120,        # 2 minutes
            'healing_actions': 180,  # 3 minutes
            'predictions': 300,      # 5 minutes
            'statistics': 60         # 1 minute
        }
        
        logger.info("MetricsCache initialized")
    
    def cache_system_status(self, status: Dict) -> bool:
        """Cache system status"""
        return self.cache.set('system:status', status, self.ttls['system_status'])
    
    def get_system_status(self) -> Optional[Dict]:
        """Get cached system status"""
        return self.cache.get('system:status')
    
    def cache_metrics(self, metrics: List[Dict], limit: int = 50) -> bool:
        """Cache metrics list"""
        key = f'metrics:recent:{limit}'
        return self.cache.set(key, metrics, self.ttls['metrics'])
    
    def get_metrics(self, limit: int = 50) -> Optional[List[Dict]]:
        """Get cached metrics"""
        key = f'metrics:recent:{limit}'
        return self.cache.get(key)
    
    def cache_anomalies(self, anomalies: List[Dict], limit: int = 20) -> bool:
        """Cache anomalies list"""
        key = f'anomalies:recent:{limit}'
        return self.cache.set(key, anomalies, self.ttls['anomalies'])
    
    def get_anomalies(self, limit: int = 20) -> Optional[List[Dict]]:
        """Get cached anomalies"""
        key = f'anomalies:recent:{limit}'
        return self.cache.get(key)
    
    def cache_healing_actions(self, actions: List[Dict], limit: int = 20) -> bool:
        """Cache healing actions list"""
        key = f'healing:recent:{limit}'
        return self.cache.set(key, actions, self.ttls['healing_actions'])
    
    def get_healing_actions(self, limit: int = 20) -> Optional[List[Dict]]:
        """Get cached healing actions"""
        key = f'healing:recent:{limit}'
        return self.cache.get(key)
    
    def cache_predictions(self, predictions: Dict) -> bool:
        """Cache predictions"""
        return self.cache.set('predictions:latest', predictions, self.ttls['predictions'])
    
    def get_predictions(self) -> Optional[Dict]:
        """Get cached predictions"""
        return self.cache.get('predictions:latest')
    
    def invalidate_metrics(self):
        """Invalidate all metrics caches"""
        self.cache.delete_pattern('metrics:*')
        self.cache.delete_pattern('anomalies:*')
        self.cache.delete_pattern('healing:*')
        self.cache.delete('system:status')
        logger.info("Metrics cache invalidated")
    
    def get_cache_info(self) -> Dict:
        """Get cache information"""
        return {
            'ttls': self.ttls,
            'keys': self.cache.keys('*'),
            'stats': self.cache.get_stats()
        }


def cached(ttl: int = 300, key_prefix: str = "cache"):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            if hasattr(func, '_cache_manager'):
                cached_value = func._cache_manager.get(cache_key)
                if cached_value is not None:
                    return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            if hasattr(func, '_cache_manager'):
                func._cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Example usage
if __name__ == '__main__':
    # Test with in-memory cache
    print("Testing CacheManager (in-memory mode)...")
    print("=" * 60)
    
    cache_manager = CacheManager(redis_client=None, default_ttl=60)
    
    # Test set/get
    print("\n1. Testing set/get:")
    cache_manager.set('test_key', {'data': 'test_value'})
    result = cache_manager.get('test_key')
    print(f"   Stored: {{'data': 'test_value'}}")
    print(f"   Retrieved: {result}")
    print(f"   Success: {result == {'data': 'test_value'}}")
    
    # Test exists
    print("\n2. Testing exists:")
    print(f"   'test_key' exists: {cache_manager.exists('test_key')}")
    print(f"   'nonexistent' exists: {cache_manager.exists('nonexistent')}")
    
    # Test stats
    print("\n3. Cache statistics:")
    stats = cache_manager.get_stats()
    print(f"   Backend: {stats['backend']}")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit rate: {stats['hit_rate']}%")
    
    # Test MetricsCache
    print("\n4. Testing MetricsCache:")
    metrics_cache = MetricsCache(cache_manager)
    
    test_status = {'health': 95.0, 'alerts': 0}
    metrics_cache.cache_system_status(test_status)
    
    retrieved_status = metrics_cache.get_system_status()
    print(f"   Cached status: {test_status}")
    print(f"   Retrieved status: {retrieved_status}")
    print(f"   Success: {retrieved_status == test_status}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")