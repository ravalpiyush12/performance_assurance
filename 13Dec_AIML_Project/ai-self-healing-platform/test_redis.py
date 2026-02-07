import redis
import sys

print("Testing Redis connection...")
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    result = r.ping()
    
    if result:
        print("✅ Redis is CONNECTED and working!")
        print(f"   Server version: {r.info('server')['redis_version']}")
        
        # Test set/get
        r.set('test_key', 'Hello from Python!')
        value = r.get('test_key')
        print(f"   Test write/read: {value}")
        r.delete('test_key')
        print("✅ All Redis operations working!")
    else:
        print("❌ Redis ping failed")
        sys.exit(1)
        
except redis.ConnectionError as e:
    print(f"❌ Cannot connect to Redis: {e}")
    print("\nTroubleshooting:")
    print("1. If using Docker: docker ps | findstr redis")
    print("2. If using Memurai: net start Memurai")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)