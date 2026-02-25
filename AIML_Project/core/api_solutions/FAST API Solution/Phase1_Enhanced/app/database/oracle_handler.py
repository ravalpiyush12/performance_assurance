"""
Oracle Connection Handler with python-oracledb (replaces cx_Oracle)
Supports both Thin mode (pure Python) and Thick mode (with Oracle Client)
"""
import oracledb
import sys
from typing import Optional


class OracleConnectionPool:
    """Manages Oracle connection pool using python-oracledb"""
    
    def __init__(self, db_config, global_settings):
        """
        Initialize Oracle connection pool
        
        Args:
            db_config: DatabaseConfig object
            global_settings: Global Settings object (for CyberArk config)
        """
        self.db_config = db_config
        self.global_settings = global_settings
        self.pool = None
        self.credentials = None
    
    def initialize(self):
        """Initialize connection pool"""
        print(f"  Initializing connection pool for {self.db_config.name}...", flush=True)
        
        # Get credentials (CyberArk or direct)
        if self.db_config.use_cyberark and self.global_settings.CYBERARK_ENABLED:
            print(f"    Using CyberArk authentication", flush=True)
            self.credentials = self._get_cyberark_credentials()
        else:
            print(f"    Using direct authentication", flush=True)
            self.credentials = {
                "username": self.db_config.username,
                "password": self.db_config.password
            }
        
        if not self.credentials.get("username") or not self.credentials.get("password"):
            raise ValueError(f"Missing credentials for {self.db_config.name}")
        
        # Build DSN
        dsn = f"{self.db_config.host}:{self.db_config.port}/{self.db_config.service_name}"
        print(f"    DSN: {dsn}", flush=True)
        
        # Create connection pool using python-oracledb
        try:
            # Create pool with Thin mode (pure Python, no Oracle Client required)
            self.pool = oracledb.create_pool(
                user=self.credentials["username"],
                password=self.credentials["password"],
                dsn=dsn,
                min=self.db_config.pool_min,
                max=self.db_config.pool_max,
                increment=self.db_config.pool_increment,
                threaded=True,
                # Thin mode parameters
                encoding="UTF-8",
                nencoding="UTF-8"
            )
            
            print(f"    Pool created: {self.db_config.pool_min}-{self.db_config.pool_max} connections", flush=True)
            print(f"    Mode: Thin (pure Python)", flush=True)
            
        except oracledb.DatabaseError as e:
            error_obj = e.args[0] if e.args else str(e)
            print(f"    Oracle Error: {error_obj}", flush=True)
            raise
    
    def _get_cyberark_credentials(self) -> dict:
        """Retrieve credentials from CyberArk"""
        from utils.cyberark import CyberArkClient
        
        cyberark = CyberArkClient(
            url=self.global_settings.CYBERARK_URL,
            app_id=self.global_settings.CYBERARK_APP_ID,
            cert_path=self.global_settings.CYBERARK_CERT_PATH,
            cert_key_path=self.global_settings.CYBERARK_CERT_KEY_PATH
        )
        
        credentials = cyberark.get_password(
            safe=self.db_config.cyberark_safe,
            object_name=self.db_config.cyberark_object
        )
        
        return {
            "username": credentials.get("UserName"),
            "password": credentials.get("Content")
        }
    
    def get_connection(self):
        """Get connection from pool"""
        if not self.pool:
            raise RuntimeError(f"Connection pool not initialized for {self.db_config.name}")
        return self.pool.acquire()
    
    def get_pool_status(self) -> dict:
        """Get pool status information"""
        if not self.pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "opened": self.pool.opened,
            "busy": self.pool.busy,
            "max": self.pool.max,
            "min": self.pool.min,
            "mode": "thin"  # python-oracledb thin mode
        }
    
    def close(self):
        """Close connection pool"""
        if self.pool:
            self.pool.close()
            self.pool = None


# Optional: Initialize Thick mode if Oracle Instant Client is available
def init_thick_mode(lib_dir: Optional[str] = None):
    """
    Initialize Thick mode (requires Oracle Instant Client)
    
    Args:
        lib_dir: Optional path to Oracle Instant Client library
    
    Note: Only call this if you need features not available in Thin mode
    (e.g., advanced Oracle features, DRCP)
    """
    try:
        if lib_dir:
            oracledb.init_oracle_client(lib_dir=lib_dir)
        else:
            oracledb.init_oracle_client()
        print("✓ Oracle Thick mode initialized", flush=True)
        return True
    except Exception as e:
        print(f"⚠ Thick mode initialization failed: {e}", flush=True)
        print("✓ Falling back to Thin mode (pure Python)", flush=True)
        return False