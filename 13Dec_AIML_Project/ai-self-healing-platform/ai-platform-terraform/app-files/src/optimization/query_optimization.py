"""
Query Optimization Module
Database query optimization and performance monitoring
"""

import time
import logging
from typing import Any, Callable, Optional, List, Dict
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """
    Monitors and logs query performance
    """
    
    def __init__(self):
        self.query_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'slow_queries': []
        })
        self.slow_query_threshold = 1.0  # seconds
    
    def record_query(self, query_name: str, execution_time: float, query_text: Optional[str] = None):
        """Record query execution statistics"""
        stats = self.query_stats[query_name]
        
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
        
        # Record slow queries
        if execution_time > self.slow_query_threshold:
            stats['slow_queries'].append({
                'time': execution_time,
                'query': query_text,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 slow queries
            if len(stats['slow_queries']) > 10:
                stats['slow_queries'] = stats['slow_queries'][-10:]
            
            logger.warning(
                f"Slow query detected: {query_name} took {execution_time:.3f}s"
            )
    
    def get_stats(self, query_name: Optional[str] = None) -> Dict:
        """Get query statistics"""
        if query_name:
            if query_name in self.query_stats:
                stats = self.query_stats[query_name]
                avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
                
                return {
                    'query_name': query_name,
                    'count': stats['count'],
                    'avg_time': round(avg_time, 3),
                    'min_time': round(stats['min_time'], 3),
                    'max_time': round(stats['max_time'], 3),
                    'slow_queries_count': len(stats['slow_queries'])
                }
            return {}
        
        # Return all stats
        result = {}
        for name, stats in self.query_stats.items():
            avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
            result[name] = {
                'count': stats['count'],
                'avg_time': round(avg_time, 3),
                'min_time': round(stats['min_time'], 3),
                'max_time': round(stats['max_time'], 3),
                'slow_queries_count': len(stats['slow_queries'])
            }
        
        return result
    
    def get_slow_queries(self, query_name: Optional[str] = None) -> List[Dict]:
        """Get slow query details"""
        if query_name:
            return self.query_stats.get(query_name, {}).get('slow_queries', [])
        
        # Return all slow queries
        all_slow = []
        for name, stats in self.query_stats.items():
            for sq in stats['slow_queries']:
                all_slow.append({
                    'query_name': name,
                    **sq
                })
        
        # Sort by time descending
        return sorted(all_slow, key=lambda x: x['time'], reverse=True)
    
    def reset_stats(self):
        """Reset all statistics"""
        self.query_stats.clear()
        logger.info("Query statistics reset")


# Global monitor instance
_query_monitor = QueryPerformanceMonitor()


def get_query_monitor() -> QueryPerformanceMonitor:
    """Get global query monitor instance"""
    return _query_monitor


def monitor_query(query_name: str):
    """
    Decorator to monitor query performance
    
    Usage:
        @monitor_query("get_user_metrics")
        def get_user_metrics(user_id: int):
            # database query
            return results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record performance
                monitor = get_query_monitor()
                monitor.record_query(query_name, execution_time)
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Query {query_name} failed after {execution_time:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator


class QueryOptimizer:
    """
    Query optimization utilities
    """
    
    @staticmethod
    def optimize_in_clause(values: List[Any], batch_size: int = 100) -> List[List[Any]]:
        """
        Split large IN clause into batches
        
        Instead of: WHERE id IN (1,2,3,...10000)
        Use: Multiple queries with smaller batches
        
        Args:
            values: List of values for IN clause
            batch_size: Maximum values per batch
            
        Returns:
            List of batches
        """
        return [values[i:i + batch_size] for i in range(0, len(values), batch_size)]
    
    @staticmethod
    def build_where_clause(filters: Dict[str, Any]) -> tuple:
        """
        Build WHERE clause from filters dictionary
        
        Args:
            filters: Dictionary of field: value pairs
            
        Returns:
            Tuple of (where_clause, params)
        """
        if not filters:
            return "", []
        
        conditions = []
        params = []
        
        for field, value in filters.items():
            if isinstance(value, (list, tuple)):
                # IN clause
                placeholders = ','.join(['?' for _ in value])
                conditions.append(f"{field} IN ({placeholders})")
                params.extend(value)
            elif value is None:
                # NULL check
                conditions.append(f"{field} IS NULL")
            else:
                # Equality
                conditions.append(f"{field} = ?")
                params.append(value)
        
        where_clause = " AND ".join(conditions)
        return f"WHERE {where_clause}", params
    
    @staticmethod
    def paginate_query(query: str, page: int, page_size: int) -> tuple:
        """
        Add pagination to query
        
        Args:
            query: Base SQL query
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Tuple of (paginated_query, offset)
        """
        offset = (page - 1) * page_size
        paginated = f"{query} LIMIT {page_size} OFFSET {offset}"
        return paginated, offset
    
    @staticmethod
    def optimize_sort(data: List[Dict], sort_field: str, ascending: bool = True) -> List[Dict]:
        """
        Optimize in-memory sorting
        
        Args:
            data: List of dictionaries
            sort_field: Field to sort by
            ascending: Sort direction
            
        Returns:
            Sorted list
        """
        return sorted(data, key=lambda x: x.get(sort_field, ''), reverse=not ascending)


class ConnectionPoolManager:
    """
    Simple connection pool manager
    """
    
    def __init__(self, min_connections: int = 2, max_connections: int = 10):
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool = []
        self.active_connections = 0
        
        logger.info(f"Connection pool initialized (min: {min_connections}, max: {max_connections})")
    
    def get_connection(self):
        """Get connection from pool"""
        if self.pool:
            conn = self.pool.pop()
            self.active_connections += 1
            logger.debug(f"Reused connection from pool (active: {self.active_connections})")
            return conn
        
        if self.active_connections < self.max_connections:
            # Create new connection (placeholder - implement actual connection)
            conn = self._create_connection()
            self.active_connections += 1
            logger.debug(f"Created new connection (active: {self.active_connections})")
            return conn
        
        logger.warning("Connection pool exhausted, waiting...")
        raise Exception("Connection pool exhausted")
    
    def release_connection(self, conn):
        """Return connection to pool"""
        if len(self.pool) < self.max_connections:
            self.pool.append(conn)
            self.active_connections -= 1
            logger.debug(f"Returned connection to pool (active: {self.active_connections})")
        else:
            # Close excess connection
            self._close_connection(conn)
            self.active_connections -= 1
    
    def _create_connection(self):
        """Create new database connection (placeholder)"""
        # Implement actual database connection here
        return {"id": time.time(), "type": "mock"}
    
    def _close_connection(self, conn):
        """Close database connection (placeholder)"""
        # Implement actual connection closing here
        pass
    
    def get_stats(self) -> Dict:
        """Get pool statistics"""
        return {
            "min_connections": self.min_connections,
            "max_connections": self.max_connections,
            "pool_size": len(self.pool),
            "active_connections": self.active_connections,
            "utilization": round((self.active_connections / self.max_connections) * 100, 2)
        }


class QueryCache:
    """
    Simple query result cache (in-memory)
    For production, use Redis via caching.py
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.access_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result"""
        if key in self.cache:
            entry = self.cache[key]
            
            # Check expiration
            if time.time() < entry['expires_at']:
                self.access_times[key] = time.time()
                logger.debug(f"Query cache HIT: {key}")
                return entry['data']
            else:
                # Expired
                del self.cache[key]
                del self.access_times[key]
        
        logger.debug(f"Query cache MISS: {key}")
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """Cache query result"""
        # Evict if full
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        self.cache[key] = {
            'data': data,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        self.access_times[key] = time.time()
        
        logger.debug(f"Query cached: {key} (TTL: {ttl}s)")
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times, key=self.access_times.get)
        del self.cache[lru_key]
        del self.access_times[lru_key]
        
        logger.debug(f"Evicted LRU entry: {lru_key}")
    
    def clear(self):
        """Clear all cached results"""
        self.cache.clear()
        self.access_times.clear()
        logger.info("Query cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization": round((len(self.cache) / self.max_size) * 100, 2)
        }


# Example usage
if __name__ == '__main__':
    import random
    
    print("\n=== Query Performance Monitoring ===")
    
    # Test query monitoring
    @monitor_query("fetch_metrics")
    def fetch_metrics(user_id: int):
        time.sleep(random.uniform(0.1, 2.0))  # Simulate query
        return {"user_id": user_id, "data": "metrics"}
    
    # Execute queries
    for i in range(10):
        fetch_metrics(i)
    
    # Get statistics
    monitor = get_query_monitor()
    stats = monitor.get_stats("fetch_metrics")
    print(f"\nQuery Stats: {stats}")
    
    # Get slow queries
    slow = monitor.get_slow_queries("fetch_metrics")
    print(f"\nSlow Queries: {len(slow)}")
    
    print("\n=== Query Optimization ===")
    
    optimizer = QueryOptimizer()
    
    # Test IN clause optimization
    large_list = list(range(1000))
    batches = optimizer.optimize_in_clause(large_list, batch_size=100)
    print(f"\nSplit 1000 IDs into {len(batches)} batches")
    
    # Test WHERE clause building
    filters = {
        "user_id": 123,
        "status": "active",
        "tags": ["python", "ml"]
    }
    where, params = optimizer.build_where_clause(filters)
    print(f"\nWHERE clause: {where}")
    print(f"Parameters: {params}")
    
    print("\n=== Connection Pool ===")
    
    pool = ConnectionPoolManager(min_connections=2, max_connections=5)
    
    # Get connections
    conns = []
    for i in range(3):
        conn = pool.get_connection()
        conns.append(conn)
    
    print(f"\nPool stats: {pool.get_stats()}")
    
    # Release connections
    for conn in conns:
        pool.release_connection(conn)
    
    print(f"After release: {pool.get_stats()}")
    
    print("\n=== Query Cache ===")
    
    query_cache = QueryCache(max_size=100, default_ttl=60)
    
    # Cache results
    query_cache.set("query_1", {"result": "data1"})
    query_cache.set("query_2", {"result": "data2"})
    
    # Retrieve
    result = query_cache.get("query_1")
    print(f"\nCached result: {result}")
    
    print(f"Cache stats: {query_cache.get_stats()}")
    
    print("\n✓ Query optimization tests completed!")