"""
Multi-Database Connection Manager
Complete implementation from architecture
"""
import sys
from typing import Dict, Optional
from config.settings import Settings, DatabaseConfig
from database.oracle_handler import OracleConnectionPool


class ConnectionManager:
    """Manages multiple Oracle database connection pools"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pools: Dict[str, OracleConnectionPool] = {}
        self.failed_databases: Dict[str, str] = {}
    
    def initialize_all(self):
        """Initialize connection pools for all configured databases"""
        print("\n" + "=" * 80, flush=True)
        print("Initializing Database Connection Pools", flush=True)
        print("=" * 80 + "\n", flush=True)
        sys.stdout.flush()
        
        databases = self.settings.get_databases()
        
        for db_name, db_config in databases.items():
            try:
                print(f"Initializing {db_name}...", flush=True)
                print(f"  Host: {db_config.host}:{db_config.port}", flush=True)
                print(f"  Service: {db_config.service_name}", flush=True)
                print(f"  Auth: {'CyberArk' if db_config.use_cyberark else 'Direct'}", flush=True)
                print(f"  Operations: {', '.join(db_config.allowed_operations)}", flush=True)
                sys.stdout.flush()
                
                pool = OracleConnectionPool(db_config, self.settings)
                pool.initialize()
                
                # Test connection
                with pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT SYSDATE FROM DUAL")
                    result = cursor.fetchone()
                    cursor.close()
                    print(f"  ✓ Connected: {result[0]}", flush=True)
                
                self.pools[db_name] = pool
                print(f"✓ {db_name} initialized successfully\n", flush=True)
                sys.stdout.flush()
                
            except Exception as e:
                print(f"✗ {db_name} initialization FAILED: {e}\n", flush=True)
                import traceback
                traceback.print_exc(file=sys.stdout)
                sys.stdout.flush()
                
                self.failed_databases[db_name] = str(e)
        
        print("=" * 80, flush=True)
        print(f"✓ Initialized {len(self.pools)}/{len(databases)} databases", flush=True)
        
        if self.failed_databases:
            print(f"⚠ Failed databases: {', '.join(self.failed_databases.keys())}", flush=True)
        
        print("=" * 80 + "\n", flush=True)
        sys.stdout.flush()
    
    def get_pool(self, db_name: str) -> Optional[OracleConnectionPool]:
        """Get connection pool for specific database"""
        return self.pools.get(db_name.upper())
    
    def is_database_available(self, db_name: str) -> bool:
        """Check if database is available"""
        return db_name.upper() in self.pools
    
    def get_available_databases(self) -> list:
        """Get list of available database names"""
        return list(self.pools.keys())
    
    def get_failed_databases(self) -> Dict[str, str]:
        """Get dict of failed databases and their errors"""
        return self.failed_databases
    
    def close_all(self):
        """Close all connection pools"""
        print("Closing all database connections...", flush=True)
        
        for db_name, pool in self.pools.items():
            try:
                pool.close()
                print(f"✓ {db_name} closed", flush=True)
            except Exception as e:
                print(f"✗ {db_name} close failed: {e}", flush=True)
        
        sys.stdout.flush()