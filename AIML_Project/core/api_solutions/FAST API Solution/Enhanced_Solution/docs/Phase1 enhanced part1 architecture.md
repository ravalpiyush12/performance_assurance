# Phase 1 Enhanced - Multi-Database Oracle SQL API with Integrated UI

## 🎯 Requirements Summary

### **Multi-Database Support (8 Databases)**

| Database | Access Type | Authentication | Allowed Operations |
|----------|-------------|----------------|-------------------|
| CQE_NFT | Read/Write | CyberArk | DQL + DML |
| CD_PTE_READ | Read-only | Direct | DQL only |
| CD_PTE_WRITE | Write | CyberArk | DML only |
| CAS_PTE_READ | Read-only | Direct | DQL only |
| CAS_PTE_WRITE | Write | CyberArk | DML only |
| PORTAL_PTE_READ | Read-only | Direct | DQL only |
| PORTAL_PTE_WRITE | Write | CyberArk | DML only |

### **Security Architecture**
- Each database has its own SECRET_KEY and VALID_API_KEYS
- CyberArk integration for all WRITE databases
- Database-specific operation restrictions (DQL/DML)
- Independent authentication per database

### **Configuration Management**
- Local: `.env.local` file
- Kubernetes/OpenShift: `values.yaml` + `deployment.yaml`

### **API Endpoints per Database**
- `/api/v1/{db_name}/execute` - Execute single SQL
- `/api/v1/{db_name}/execute-file` - Execute multiple queries from file
- `/api/v1/{db_name}/health` - Database-specific health check

### **Integrated Web UI (Tab-Based)**
- Tab 1: Oracle SQL API (with database selector)
- Tab 2: AppDynamics Monitoring
- Tab 3: Kibana Monitoring
- Tab 4: Splunk Monitoring
- Tab 5: MongoDB Monitoring
- Live API testing with pre-populated API keys
- Interactive API documentation
- Request/response examples

---

## 📁 Project Structure (Enhanced)

```
oracle-sql-api/
├── app/
│   ├── main.py                          # Main FastAPI app with UI
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                  # Multi-database settings
│   │   └── database_config.py           # Database-specific configs
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py                  # Multi-database security
│   │   └── sql_validator.py             # DQL/DML validation
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection_manager.py        # Multi-database pool manager
│   │   ├── oracle_handler.py            # Oracle connection handler
│   │   └── sql_executor.py              # SQL execution with validation
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py              # Database-specific dependencies
│   │   ├── oracle_routes.py             # Dynamic routes per database
│   │   ├── monitoring_routes.py         # Monitoring endpoints
│   │   └── health_routes.py             # Health check endpoints
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── static/
│   │   │   ├── css/
│   │   │   │   └── styles.css
│   │   │   └── js/
│   │   │       └── app.js
│   │   └── templates/
│   │       └── index.html               # Tab-based UI
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py                  # Request models
│   │   └── responses.py                 # Response models
│   └── utils/
│       ├── __init__.py
│       ├── audit.py                     # Audit logging
│       └── cyberark.py                  # CyberArk integration
├── config/
│   ├── .env.local.example               # Example local config
│   └── databases.yaml                   # Database metadata
├── kubernetes/
│   ├── values.yaml                      # Helm values (multi-db)
│   └── deployment.yaml                  # K8s deployment
├── requirements.txt
├── Dockerfile
├── gunicorn.conf.py
└── README.md
```

---

## 🛠️ Implementation Files

### **1. Enhanced Settings (config/settings.py)**

```python
"""
Multi-Database Configuration Settings - Pydantic v1
Supports 8 Oracle databases with individual credentials and API keys
"""
from pydantic import BaseSettings, Field, validator
from typing import Dict, List, Optional
from functools import lru_cache
import os
import json


class DatabaseConfig(BaseSettings):
    """Individual database configuration"""
    name: str
    host: str
    port: int = 1521
    service_name: str
    username: Optional[str] = None
    password: Optional[str] = None
    use_cyberark: bool = False
    allowed_operations: List[str]  # ["DQL"] or ["DML"] or ["DQL", "DML"]
    secret_key: str
    api_keys: str  # Comma-separated
    
    # Connection pool settings
    pool_min: int = 2
    pool_max: int = 10
    pool_increment: int = 1
    
    # CyberArk settings (if use_cyberark=True)
    cyberark_safe: Optional[str] = None
    cyberark_object: Optional[str] = None
    
    def get_api_keys_list(self) -> List[str]:
        """Parse API keys into list"""
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]
    
    class Config:
        env_file = None
        case_sensitive = True


class Settings(BaseSettings):
    """Application Settings with Multi-Database Support"""
    
    # Application Settings
    APP_NAME: str = "Oracle SQL API - Multi-Database"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "local"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Global CyberArk Settings
    CYBERARK_ENABLED: bool = False
    CYBERARK_URL: Optional[str] = None
    CYBERARK_APP_ID: Optional[str] = None
    CYBERARK_CERT_PATH: Optional[str] = None
    CYBERARK_CERT_KEY_PATH: Optional[str] = None
    
    # SQL Execution Settings
    MAX_SQL_FILE_SIZE_MB: int = 10
    SQL_EXECUTION_TIMEOUT: int = 300
    
    # Audit Settings
    ENABLE_AUDIT_LOG: bool = True
    AUDIT_LOG_PATH: str = "/app/logs/audit"
    
    # Database Configurations (JSON string from env)
    DATABASES_CONFIG: str = "{}"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600
    
    class Config:
        env_file = None
        case_sensitive = True
    
    @validator('DATABASES_CONFIG', pre=True)
    def validate_databases_config(cls, v):
        """Validate databases config is valid JSON"""
        if isinstance(v, str):
            try:
                json.loads(v)
                return v
            except json.JSONDecodeError:
                raise ValueError("DATABASES_CONFIG must be valid JSON")
        return json.dumps(v)
    
    def get_databases(self) -> Dict[str, DatabaseConfig]:
        """Parse and return database configurations"""
        configs = json.loads(self.DATABASES_CONFIG)
        
        databases = {}
        for db_name, db_config in configs.items():
            databases[db_name] = DatabaseConfig(
                name=db_name,
                **db_config
            )
        
        return databases
    
    def get_database(self, db_name: str) -> Optional[DatabaseConfig]:
        """Get specific database configuration"""
        databases = self.get_databases()
        return databases.get(db_name.upper())


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    import sys
    
    print("Loading multi-database settings...", flush=True)
    settings = Settings()
    
    databases = settings.get_databases()
    print(f"✓ Settings loaded: {settings.ENVIRONMENT} v{settings.APP_VERSION}", flush=True)
    print(f"✓ Databases configured: {len(databases)}", flush=True)
    
    for db_name, db_config in databases.items():
        print(f"  - {db_name}: {db_config.host}:{db_config.port}/{db_config.service_name}", flush=True)
        print(f"    Operations: {', '.join(db_config.allowed_operations)}", flush=True)
        print(f"    Auth: {'CyberArk' if db_config.use_cyberark else 'Direct'}", flush=True)
    
    sys.stdout.flush()
    return settings
```

---

### **2. Database Configuration Manager (config/database_config.py)**

```python
"""
Database Configuration Manager
Handles configuration for all 8 Oracle databases
"""
from typing import Dict
import os


def get_databases_config() -> Dict:
    """
    Generate database configurations for all 8 databases
    Reads from environment variables
    """
    
    databases = {}
    
    # Database names
    db_names = [
        "CQE_NFT",
        "CD_PTE_READ",
        "CD_PTE_WRITE",
        "CAS_PTE_READ",
        "CAS_PTE_WRITE",
        "PORTAL_PTE_READ",
        "PORTAL_PTE_WRITE"
    ]
    
    for db_name in db_names:
        prefix = db_name.replace("-", "_").upper()
        
        # Determine if it's a write database (uses CyberArk)
        is_write = "WRITE" in db_name or db_name == "CQE_NFT"
        
        # Determine allowed operations
        if db_name == "CQE_NFT":
            allowed_ops = ["DQL", "DML"]
        elif "READ" in db_name:
            allowed_ops = ["DQL"]
        else:  # WRITE
            allowed_ops = ["DML"]
        
        db_config = {
            "host": os.getenv(f"{prefix}_HOST"),
            "port": int(os.getenv(f"{prefix}_PORT", "1521")),
            "service_name": os.getenv(f"{prefix}_SERVICE_NAME"),
            "username": os.getenv(f"{prefix}_USERNAME"),
            "password": os.getenv(f"{prefix}_PASSWORD"),
            "use_cyberark": is_write and os.getenv("CYBERARK_ENABLED", "false").lower() == "true",
            "allowed_operations": allowed_ops,
            "secret_key": os.getenv(f"{prefix}_SECRET_KEY"),
            "api_keys": os.getenv(f"{prefix}_API_KEYS"),
            "pool_min": int(os.getenv(f"{prefix}_POOL_MIN", "2")),
            "pool_max": int(os.getenv(f"{prefix}_POOL_MAX", "10")),
            "pool_increment": int(os.getenv(f"{prefix}_POOL_INCREMENT", "1")),
        }
        
        # Add CyberArk settings for write databases
        if is_write:
            db_config["cyberark_safe"] = os.getenv(f"{prefix}_CYBERARK_SAFE")
            db_config["cyberark_object"] = os.getenv(f"{prefix}_CYBERARK_OBJECT")
        
        databases[db_name] = db_config
    
    return databases
```

---

### **3. SQL Validator (core/sql_validator.py)**

```python
"""
SQL Validator - Enforces DQL/DML restrictions per database
"""
import re
from typing import List, Tuple
from enum import Enum


class SQLOperationType(str, Enum):
    """SQL operation types"""
    DQL = "DQL"  # Data Query Language (SELECT)
    DML = "DML"  # Data Manipulation Language (INSERT, UPDATE, DELETE)
    DDL = "DDL"  # Data Definition Language (CREATE, ALTER, DROP, TRUNCATE)
    DCL = "DCL"  # Data Control Language (GRANT, REVOKE)


class SQLValidator:
    """Validates SQL statements based on allowed operations"""
    
    # DQL keywords
    DQL_KEYWORDS = ["SELECT", "WITH"]
    
    # DML keywords
    DML_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "MERGE"]
    
    # DDL keywords (always blocked)
    DDL_KEYWORDS = [
        "CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME",
        "COMMENT", "FLASHBACK", "PURGE"
    ]
    
    # DCL keywords (always blocked)
    DCL_KEYWORDS = ["GRANT", "REVOKE"]
    
    # Dangerous patterns (always blocked)
    DANGEROUS_PATTERNS = [
        r";\s*DROP\s+",
        r";\s*DELETE\s+FROM\s+",
        r";\s*TRUNCATE\s+",
        r"--\s*DROP",
        r"/\*.*DROP.*\*/",
    ]
    
    @staticmethod
    def detect_operation_type(sql: str) -> SQLOperationType:
        """Detect the type of SQL operation"""
        sql_upper = sql.strip().upper()
        
        # Remove comments
        sql_upper = re.sub(r'--.*$', '', sql_upper, flags=re.MULTILINE)
        sql_upper = re.sub(r'/\*.*?\*/', '', sql_upper, flags=re.DOTALL)
        
        # Get first keyword
        first_keyword = sql_upper.split()[0] if sql_upper.split() else ""
        
        if first_keyword in SQLValidator.DQL_KEYWORDS:
            return SQLOperationType.DQL
        elif first_keyword in SQLValidator.DML_KEYWORDS:
            return SQLOperationType.DML
        elif first_keyword in SQLValidator.DDL_KEYWORDS:
            return SQLOperationType.DDL
        elif first_keyword in SQLValidator.DCL_KEYWORDS:
            return SQLOperationType.DCL
        else:
            # Default to DML for unknown (safer to block)
            return SQLOperationType.DML
    
    @staticmethod
    def validate_sql(sql: str, allowed_operations: List[str]) -> Tuple[bool, str]:
        """
        Validate SQL against allowed operations
        
        Returns:
            (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty SQL statement"
        
        # Check for dangerous patterns first
        for pattern in SQLValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                return False, f"SQL contains dangerous pattern: {pattern}"
        
        # Detect operation type
        op_type = SQLValidator.detect_operation_type(sql)
        
        # Check if operation is DDL or DCL (always blocked)
        if op_type in [SQLOperationType.DDL, SQLOperationType.DCL]:
            return False, f"{op_type.value} operations are not allowed"
        
        # Check if operation is allowed for this database
        if op_type.value not in allowed_operations:
            return False, f"{op_type.value} operations not allowed for this database. Allowed: {', '.join(allowed_operations)}"
        
        return True, ""
    
    @staticmethod
    def validate_multiple_sql(sql_statements: List[str], allowed_operations: List[str]) -> Tuple[bool, str, List[str]]:
        """
        Validate multiple SQL statements
        
        Returns:
            (all_valid, error_message, failed_statements)
        """
        failed = []
        
        for i, sql in enumerate(sql_statements, 1):
            is_valid, error_msg = SQLValidator.validate_sql(sql, allowed_operations)
            if not is_valid:
                failed.append(f"Statement {i}: {error_msg}")
        
        if failed:
            return False, "\n".join(failed), failed
        
        return True, "", []
```

---

### **4. Multi-Database Connection Manager (database/connection_manager.py)**

```python
"""
Multi-Database Connection Manager
Manages connection pools for all 8 Oracle databases
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
```

---

This is Part 1 of the implementation. Would you like me to continue with:

1. **Part 2**: Enhanced main.py with tab-based UI
2. **Part 3**: Dynamic API routes for all databases
3. **Part 4**: Configuration files (.env.local.example, values.yaml, deployment.yaml)
4. **Part 5**: Complete HTML/CSS/JS for the integrated UI

Which part would you like next?