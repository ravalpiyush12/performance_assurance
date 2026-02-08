# Oracle SQL API - Complete Project Structure

```
oracle-sql-api/
│
├── 📁 Core Application Files
│   ├── main.py                           # FastAPI application & API endpoints
│   ├── config.py                         # Configuration management (Settings class)
│   ├── cyberark_provider.py              # CyberArk credential provider integration
│   ├── oracle_handler.py                 # Oracle connection pool & SQL executor
│   ├── security.py                       # Authentication, JWT, rate limiting
│   └── audit.py                          # Audit logging system
│
├── 📁 Configuration Files
│   ├── .env.template                     # Environment variables template
│   ├── .env.local                        # Local development config (git ignored)
│   └── .gitignore                        # Git ignore rules
│
├── 📁 Docker & Containerization
│   ├── Dockerfile                        # Multi-stage Docker build
│   ├── docker-compose.yml                # Local Docker deployment
│   └── requirements.txt                  # Python dependencies
│
├── 📁 AWS ECS Deployment
│   ├── ecs-task-definition.json          # ECS Fargate task definition
│   └── deploy-to-ecs.sh                  # Automated deployment script
│
├── 📁 Testing & Development
│   ├── test_api.py                       # Comprehensive test suite
│   ├── sample.sql                        # Sample SQL for testing
│   ├── setup.sh                          # Development setup script
│   └── Oracle_SQL_API.postman_collection.json  # Postman API collection
│
├── 📁 Documentation
│   ├── README.md                         # Complete user guide
│   └── ARCHITECTURE.md                   # Technical architecture docs
│
└── 📁 Runtime (Created automatically)
    └── logs/
        └── audit/
            └── audit_YYYYMMDD.jsonl      # Daily audit logs
```

## 📋 Detailed File Descriptions

### Core Application Layer

#### **main.py** (Main Application)
```
Lines: ~400
Purpose: FastAPI application entry point
Components:
  ├── FastAPI app initialization
  ├── CORS middleware configuration
  ├── Pydantic request/response models
  ├── API endpoints (8 endpoints)
  ├── Startup/shutdown lifecycle
  ├── Error handlers
  └── Dependency injection setup

Key Endpoints:
  • GET  /                          - Root endpoint
  • GET  /health                    - Health check
  • POST /api/v1/auth/token         - Generate JWT token
  • POST /api/v1/sql/execute        - Execute SQL
  • POST /api/v1/sql/execute-file   - Execute SQL file
  • GET  /api/v1/audit/summary      - Audit summary
  • GET  /api/v1/rate-limit/status  - Rate limit info
  • GET  /api/v1/pool/status        - Pool status
```

#### **config.py** (Configuration Management)
```
Lines: ~130
Purpose: Centralized configuration with Pydantic Settings
Components:
  ├── Settings class (environment-based)
  ├── Configuration validation
  ├── Default values
  ├── Environment templates
  └── Helper methods

Configuration Categories:
  • Application (name, version, environment)
  • Security (keys, tokens, algorithms)
  • Oracle Database (host, port, credentials)
  • CyberArk (URL, App ID, Safe, Object)
  • SQL Execution (file size, timeout, allowed ops)
  • Audit (logging, path)
  • AWS (region, ECS settings)
```

#### **cyberark_provider.py** (Credential Provider)
```
Lines: ~170
Purpose: Secure credential retrieval
Components:
  ├── OracleCredentials (dataclass)
  ├── CyberArkProvider (AIM API client)
  └── CredentialManager (unified interface)

Features:
  • Certificate-based authentication
  • Environment-aware (local vs prod)
  • Session management
  • Error handling & logging
  • Credential caching
```

#### **oracle_handler.py** (Database Handler)
```
Lines: ~270
Purpose: Oracle database operations
Components:
  ├── OracleConnectionPool
  │   ├── Pool initialization
  │   ├── Connection management
  │   ├── Health checks
  │   └── Pool statistics
  │
  └── SQLExecutor
      ├── SQL validation
      ├── Operation detection
      ├── Query execution (SELECT)
      ├── DML execution (INSERT/UPDATE/DELETE)
      ├── Transaction management
      └── Result formatting

SQL Validation Rules:
  ✓ Allowed: SELECT, INSERT, UPDATE, DELETE, MERGE
  ✗ Blocked: DROP, TRUNCATE, ALTER, CREATE, GRANT, REVOKE
```

#### **security.py** (Security Layer)
```
Lines: ~240
Purpose: Authentication & authorization
Components:
  ├── RateLimiter (in-memory)
  │   ├── Request tracking
  │   ├── Time-window based
  │   └── Per-identifier limits
  │
  ├── TokenManager (JWT)
  │   ├── Token creation
  │   ├── Token verification
  │   └── Expiration handling
  │
  └── SecurityManager (unified)
      ├── API key validation
      ├── Token verification
      ├── Rate limit checking
      └── FastAPI dependencies

Security Features:
  • Multi-factor (API key + optional JWT)
  • Configurable rate limits
  • Thread-safe operations
  • Request identification (API key or IP)
```

#### **audit.py** (Audit Logging)
```
Lines: ~200
Purpose: Comprehensive audit trail
Components:
  ├── AuditLogger
  │   ├── Request logging
  │   ├── Response logging
  │   ├── Authentication logging
  │   └── Summary generation

Log Format: JSONL (JSON Lines)
  {
    "timestamp": "2024-02-07T10:30:00",
    "event_type": "sql_request",
    "request_id": "abc-123",
    "username": "john_doe",
    "operation_type": "SELECT",
    "sql_preview": "SELECT * FROM...",
    "client_ip": "192.168.1.1"
  }

Log Types:
  • sql_request    - SQL execution request
  • sql_response   - SQL execution result
  • authentication - Auth attempts
```

---

### Configuration Layer

#### **.env.template** (Environment Template)
```
Purpose: Configuration template for all environments
Sections:
  • Environment settings
  • Security keys
  • Oracle credentials (local)
  • CyberArk settings (production)
  • Rate limiting
  • SQL execution parameters
  • Audit logging
  • AWS configuration

Usage: Copy to .env and customize
```

#### **.env.local** (Local Development)
```
Purpose: Local development configuration
Features:
  • Debug enabled
  • Local Oracle credentials
  • CyberArk disabled
  • Relaxed rate limits
  • Local audit logging

⚠️  Git Ignored - Never commit this file
```

#### **.gitignore** (Git Ignore Rules)
```
Excludes:
  • Python cache (__pycache__, *.pyc)
  • Virtual environments (venv/, env/)
  • Environment files (.env, .env.*)
  • Logs (logs/, *.log, audit_*.jsonl)
  • IDE files (.vscode/, .idea/)
  • OS files (.DS_Store, Thumbs.db)
  • Docker overrides
  • AWS credentials
  • Test artifacts
```

---

### Docker & Containerization Layer

#### **Dockerfile** (Container Image)
```
Type: Multi-stage build
Base Image: python:3.11-slim
Stages:
  1. Builder Stage
     ├── Install Oracle Instant Client 21.15
     ├── Configure library paths
     └── Prepare dependencies
  
  2. Production Stage
     ├── Copy Oracle libraries
     ├── Install Python dependencies
     ├── Copy application code
     ├── Create non-root user
     ├── Setup logs directory
     └── Configure health check

Container Configuration:
  • Port: 8000
  • User: appuser (non-root)
  • Health Check: Every 30s
  • CMD: Gunicorn with 4 workers
  • Worker Class: Uvicorn workers
```

#### **docker-compose.yml** (Local Deployment)
```
Services:
  oracle-sql-api:
    ├── Build from Dockerfile
    ├── Port mapping: 8000:8000
    ├── Environment from .env.local
    ├── Volume mounts: logs/
    ├── Restart policy: unless-stopped
    ├── Health checks enabled
    └── Network: oracle-network

Usage:
  $ docker-compose up -d      # Start
  $ docker-compose logs -f    # View logs
  $ docker-compose down       # Stop
```

#### **requirements.txt** (Python Dependencies)
```
Core Framework:
  • fastapi==0.109.0          - REST API framework
  • uvicorn==0.27.0           - ASGI server
  • gunicorn==21.2.0          - WSGI server (production)
  • pydantic==2.5.3           - Data validation

Database:
  • cx_Oracle==8.3.0          - Oracle driver

Security:
  • python-jose==3.3.0        - JWT tokens
  • passlib==1.7.4            - Password hashing
  • bcrypt==4.1.2             - Encryption

Utilities:
  • requests==2.31.0          - HTTP client (CyberArk)
  • python-dotenv==1.0.0      - Environment variables
  • structlog==24.1.0         - Structured logging
```

---

### AWS ECS Deployment Layer

#### **ecs-task-definition.json** (ECS Configuration)
```
Configuration:
  Family: oracle-sql-api
  Launch Type: Fargate
  CPU: 1024 (1 vCPU)
  Memory: 2048 MB
  Network Mode: awsvpc

Container Definition:
  ├── Image: ECR repository
  ├── Port: 8000
  ├── Environment Variables (non-sensitive)
  ├── Secrets (from AWS Secrets Manager)
  │   ├── SECRET_KEY
  │   ├── VALID_API_KEYS
  │   └── CyberArk credentials
  ├── CloudWatch Logs
  │   ├── Log Group: /ecs/oracle-sql-api
  │   └── Stream Prefix: ecs
  └── Health Check
      ├── Command: curl health endpoint
      ├── Interval: 30s
      └── Start Period: 60s

IAM Roles Required:
  • ecsTaskExecutionRole - ECR & Secrets Manager access
  • oracleSqlApiTaskRole - Application permissions
```

#### **deploy-to-ecs.sh** (Deployment Script)
```bash
Purpose: Automated ECS deployment
Steps:
  1. Build Docker image locally
  2. Login to Amazon ECR
  3. Tag image with timestamp
  4. Push to ECR repository
  5. Update ECS task definition
  6. Update ECS service
  7. Wait for service stability

Configuration Required:
  • AWS_ACCOUNT_ID
  • AWS_REGION
  • ECR_REPOSITORY
  • ECS_CLUSTER
  • ECS_SERVICE

Features:
  • Colored output
  • Error handling (set -e)
  • Image versioning (timestamp tags)
  • Service stability wait
  • Rollback on failure

Usage:
  $ chmod +x deploy-to-ecs.sh
  $ ./deploy-to-ecs.sh
```

---

### Testing & Development Layer

#### **test_api.py** (Test Suite)
```
Lines: ~350
Purpose: Comprehensive API testing
Test Categories:
  1. Health Check
  2. Root Endpoint
  3. Authentication (JWT token)
  4. SQL SELECT Query
  5. SQL Validation (security)
  6. Rate Limit Status
  7. Connection Pool Status
  8. Unauthorized Access
  9. SQL File Upload

Features:
  • Colored output (✓/✗)
  • Test summary statistics
  • Detailed error reporting
  • Sequential execution
  • Request/response validation

Usage:
  $ python test_api.py
  
Output:
  ✓ PASS - Health Check
  ✓ PASS - SQL SELECT
  ✗ FAIL - Invalid Test
  
  Summary: 8/9 tests passed (88.9%)
```

#### **sample.sql** (Test SQL File)
```sql
Purpose: Sample SQL for testing file upload
Contents:
  • Query 1: Current date and user
  • Query 2: Database version
  • Query 3: Object aggregation

Usage:
  Upload via /api/v1/sql/execute-file endpoint
```

#### **setup.sh** (Development Setup)
```bash
Purpose: Automated development environment setup
Steps:
  1. Check Python version (3.11+)
  2. Create virtual environment
  3. Activate venv
  4. Upgrade pip
  5. Install dependencies
  6. Create .env from template
  7. Create logs directory
  8. Make scripts executable
  9. Test imports

Output:
  ✓ Python 3.11.0
  ✓ Virtual environment created
  ✓ Dependencies installed
  ✓ .env file created
  
  Next steps:
  1. Edit .env with credentials
  2. Run: python main.py
  3. Test: python test_api.py

Usage:
  $ chmod +x setup.sh
  $ ./setup.sh
```

#### **Oracle_SQL_API.postman_collection.json** (API Collection)
```
Purpose: Postman collection for API testing
Variables:
  • base_url: http://localhost:8000
  • api_key: local-dev-api-key
  • username: test_user

Requests (11 total):
  1. Health Check
  2. Get Auth Token (saves token)
  3. Execute SELECT Query
  4. Execute INSERT Query
  5. Execute UPDATE Query
  6. Execute SQL File
  7. Get Pool Status
  8. Get Rate Limit Status
  9. Get Audit Summary
  10. Test Invalid SQL (DROP - should fail)
  11. Test Unauthorized Access

Import: File > Import > Oracle_SQL_API.postman_collection.json
```

---

### Documentation Layer

#### **README.md** (User Guide)
```
Sections:
  1. Features Overview
  2. Architecture Diagram
  3. Quick Start Guide
     ├── Local Development
     ├── Docker Deployment
     └── AWS ECS Deployment
  4. API Documentation
     ├── Authentication
     ├── Endpoints
     └── Error Responses
  5. Configuration Reference
  6. Monitoring & Logging
  7. Security Best Practices
  8. Troubleshooting
  9. Future Enhancements

Target Audience: Developers, DevOps Engineers
```

#### **ARCHITECTURE.md** (Technical Docs)
```
Sections:
  1. Directory Structure
  2. Module Descriptions (detailed)
  3. Data Flow Diagrams
  4. Configuration Files
  5. Security Architecture
  6. Deployment Architecture
  7. Error Handling Strategy
  8. Monitoring Strategy
  9. Extension Points
  10. Best Practices
  11. Performance Considerations
  12. Scaling Considerations

Target Audience: Architects, Senior Engineers
```

---

### Runtime Layer (Auto-generated)

#### **logs/** (Log Directory)
```
logs/
└── audit/
    ├── audit_20240207.jsonl    # Today's audit log
    ├── audit_20240206.jsonl    # Yesterday's audit log
    └── audit_20240205.jsonl    # Day before yesterday

Format: JSONL (JSON Lines)
  • One JSON object per line
  • Easy to parse programmatically
  • Append-only for performance
  • Daily rotation

Example Entry:
  {
    "timestamp": "2024-02-07T10:30:00.123456",
    "event_type": "sql_request",
    "request_id": "abc-123-def-456",
    "username": "john_doe",
    "api_key_masked": "abcd...wxyz",
    "operation_type": "SELECT",
    "sql_preview": "SELECT * FROM employees...",
    "client_ip": "192.168.1.100",
    "metadata": {
      "description": "Monthly report query"
    }
  }
```

---

## 📊 File Statistics

```
Total Files:     20
Total Lines:     ~3,500

Breakdown by Type:
  Python:        ~2,000 lines (6 files)
  Configuration: ~200 lines (5 files)
  Docker:        ~150 lines (3 files)
  Documentation: ~800 lines (2 files)
  Scripts:       ~250 lines (2 files)
  Tests:         ~350 lines (2 files)
```

---

## 🔄 Data Flow Through Files

### Request Flow:
```
1. Client Request
   ↓
2. main.py (FastAPI endpoint)
   ↓
3. security.py (Verify API key & rate limit)
   ↓
4. audit.py (Log request)
   ↓
5. oracle_handler.py (Validate & execute SQL)
   ↓
6. cyberark_provider.py (Get credentials - if needed)
   ↓
7. cx_Oracle (Oracle database connection)
   ↓
8. oracle_handler.py (Format results)
   ↓
9. audit.py (Log response)
   ↓
10. main.py (Return response)
```

### Startup Flow:
```
1. main.py (App startup event)
   ↓
2. config.py (Load settings)
   ↓
3. security.py (Initialize SecurityManager)
   ↓
4. audit.py (Initialize AuditLogger)
   ↓
5. cyberark_provider.py (Get credentials)
   ↓
6. oracle_handler.py (Initialize connection pool)
   ↓
7. oracle_handler.py (Test connection)
   ↓
8. main.py (Ready to accept requests)
```

---

## 🎯 Quick Reference

### Local Development:
```bash
./setup.sh              # Initial setup
python main.py          # Start API
python test_api.py      # Run tests
```

### Docker:
```bash
docker-compose up -d    # Start
docker-compose logs -f  # View logs
docker-compose down     # Stop
```

### AWS ECS:
```bash
./deploy-to-ecs.sh      # Deploy to ECS
```

### Configuration:
```bash
.env.local              # Local config
.env.template           # Template
ecs-task-definition.json # ECS config
```

---

**Last Updated**: February 2024
**Version**: 1.0.0