# Oracle SQL API - Project Structure

## Directory Structure

```
oracle-sql-api/
├── main.py                          # FastAPI application entry point
├── config.py                        # Configuration management
├── cyberark_provider.py            # CyberArk credential provider
├── oracle_handler.py               # Oracle connection pool & SQL executor
├── security.py                     # Authentication & authorization
├── audit.py                        # Audit logging
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker image definition
├── docker-compose.yml              # Local Docker deployment
├── ecs-task-definition.json       # ECS task definition
├── deploy-to-ecs.sh               # ECS deployment script
├── setup.sh                       # Setup script
├── test_api.py                    # Test suite
├── .env.template                  # Environment template
├── .env.local                     # Local environment (git ignored)
├── .gitignore                     # Git ignore rules
├── README.md                      # Main documentation
├── ARCHITECTURE.md                # This file
├── Oracle_SQL_API.postman_collection.json  # Postman collection
└── logs/                          # Log directory
    └── audit/                     # Audit logs
        └── audit_YYYYMMDD.jsonl
```

## Module Descriptions

### main.py
**Purpose**: FastAPI application with all API endpoints

**Key Components**:
- FastAPI app initialization
- CORS middleware configuration
- API endpoint definitions
- Request/Response models (Pydantic)
- Startup/shutdown lifecycle management
- Error handlers
- Health checks

**Endpoints**:
- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/auth/token` - Generate JWT token
- `POST /api/v1/sql/execute` - Execute SQL
- `POST /api/v1/sql/execute-file` - Execute SQL file
- `GET /api/v1/audit/summary` - Get audit summary
- `GET /api/v1/rate-limit/status` - Rate limit status
- `GET /api/v1/pool/status` - Connection pool status

### config.py
**Purpose**: Centralized configuration management

**Key Features**:
- Pydantic Settings for type-safe configuration
- Environment-specific settings (local/dev/prod)
- Configuration validation
- Default values
- Environment variable loading

**Configuration Categories**:
- Application settings (name, version, environment)
- Security settings (keys, tokens, algorithms)
- Oracle database settings
- CyberArk settings
- SQL execution settings
- Audit settings
- AWS settings

### cyberark_provider.py
**Purpose**: Secure credential retrieval from CyberArk

**Key Components**:
- `OracleCredentials`: Data class for DB credentials
- `CyberArkProvider`: CyberArk AIM API integration
- `CredentialManager`: Unified credential management

**Features**:
- Certificate-based authentication
- Environment-based credential selection (CyberArk vs local)
- Error handling and logging
- Session management

### oracle_handler.py
**Purpose**: Oracle database connection and SQL execution

**Key Components**:
- `OracleConnectionPool`: Connection pool manager
- `SQLExecutor`: SQL validation and execution

**Features**:
- cx_Oracle connection pooling
- SQL validation and sanitization
- Operation type detection
- Query result formatting
- DML transaction management
- Execution time tracking
- Error handling

**SQL Validation**:
- Allowed operations: SELECT, INSERT, UPDATE, DELETE, MERGE
- Blocked operations: DROP, TRUNCATE, ALTER, CREATE, GRANT, REVOKE
- Dangerous pattern detection
- Comment removal

### security.py
**Purpose**: Authentication, authorization, and rate limiting

**Key Components**:
- `RateLimiter`: In-memory rate limiting
- `TokenManager`: JWT token creation/verification
- `SecurityManager`: Unified security management

**Features**:
- API key validation
- JWT token support
- Rate limiting (configurable)
- FastAPI dependencies for endpoint protection
- Request identification (API key or IP)

### audit.py
**Purpose**: Comprehensive audit logging

**Key Features**:
- JSONL format (one JSON per line)
- Date-based log files
- Automatic log rotation
- Audit summary generation

**Logged Events**:
- SQL requests (user, SQL preview, operation type)
- SQL responses (status, rows affected, execution time)
- Authentication attempts
- All requests include timestamp, request ID, client IP

**Audit Summary**:
- Total/successful/failed requests
- Operations breakdown
- Unique users
- Date-based queries

## Data Flow

### 1. SQL Execution Flow

```
Client Request
    ↓
[FastAPI Endpoint] → Validate API Key
    ↓
[Security Manager] → Check Rate Limit
    ↓
[Audit Logger] → Log Request
    ↓
[SQL Executor] → Validate SQL
    ↓
[Connection Pool] → Get Connection
    ↓
[Oracle Database] → Execute SQL
    ↓
[SQL Executor] → Format Results
    ↓
[Audit Logger] → Log Response
    ↓
Client Response
```

### 2. Authentication Flow

```
Client (username + API key)
    ↓
[Security Manager] → Verify API Key
    ↓
[Token Manager] → Generate JWT
    ↓
[Audit Logger] → Log Auth Event
    ↓
Client (JWT token)
```

### 3. Connection Pool Initialization

```
App Startup
    ↓
[Credential Manager] → Check Environment
    ↓
    ├─[Local] → Read from .env
    └─[Prod] → CyberArk API Call
    ↓
[Connection Pool] → Initialize Pool
    ↓
[Connection Pool] → Test Connection
    ↓
Ready for Requests
```

## Configuration Files

### .env (Local Development)
```env
ENVIRONMENT=local
DEBUG=true
ORACLE_HOST=localhost
ORACLE_USERNAME=system
ORACLE_PASSWORD=oracle
SECRET_KEY=local-dev-key
VALID_API_KEYS=local-api-key
```

### ECS Task Definition
- Environment: prod
- Secrets from AWS Secrets Manager
- CyberArk enabled
- CloudWatch logging
- Health checks

## Security Architecture

### Defense Layers

1. **Network Layer**
   - VPC security groups (ECS)
   - Load balancer rules
   - HTTPS/TLS

2. **Application Layer**
   - API key authentication
   - JWT tokens (optional)
   - Rate limiting
   - SQL validation

3. **Data Layer**
   - CyberArk credential management
   - Encrypted secrets (AWS Secrets Manager)
   - Connection pooling with credentials rotation

4. **Audit Layer**
   - Comprehensive logging
   - Request/response tracking
   - Authentication logging

## Deployment Architecture

### Local Development
```
Docker Container
    ↓
FastAPI + Gunicorn
    ↓
cx_Oracle
    ↓
Local Oracle DB
```

### AWS ECS Production
```
ALB (Load Balancer)
    ↓
ECS Fargate Tasks
    ├─ Container 1
    ├─ Container 2
    └─ Container N
    ↓
CyberArk (credentials)
    ↓
Oracle Database
    ↓
CloudWatch (logs/metrics)
```

## Error Handling Strategy

### Application Errors
- Graceful degradation
- Detailed error messages (dev)
- Generic error messages (prod)
- Error codes and HTTP status

### Database Errors
- Connection retry logic
- Transaction rollback
- Error logging
- Pool recovery

### Security Errors
- Failed authentication logging
- Rate limit violations
- Invalid SQL detection
- Audit trail

## Monitoring Strategy

### Health Checks
- Database connectivity
- Connection pool status
- Application status
- Response time

### Metrics
- Request rate
- Error rate
- SQL execution time
- Connection pool utilization
- Rate limit hits

### Alerts (Recommended)
- Database connection failures
- High error rates
- Rate limit violations
- Authentication failures
- Long-running queries

## Extension Points

### Adding New Monitoring APIs
Following your requirement for AppDynamics and Kibana monitoring APIs:

1. Create new module: `monitoring_handler.py`
```python
class MonitoringManager:
    def start_appdynamics_monitoring(...)
    def stop_appdynamics_monitoring(...)
    def start_kibana_monitoring(...)
    def stop_kibana_monitoring(...)
```

2. Add endpoints in `main.py`:
```python
@app.post("/api/v1/monitoring/appdynamics/start")
@app.post("/api/v1/monitoring/appdynamics/stop")
@app.post("/api/v1/monitoring/kibana/start")
@app.post("/api/v1/monitoring/kibana/stop")
```

3. Reuse existing infrastructure:
   - Security: Same API key authentication
   - Audit: Same logging mechanism
   - Configuration: Add to config.py

## Best Practices

### Code Organization
- ✅ Separation of concerns (modules)
- ✅ Type hints throughout
- ✅ Comprehensive error handling
- ✅ Logging at appropriate levels
- ✅ Configuration-driven design

### Security
- ✅ No hardcoded credentials
- ✅ Environment-based configuration
- ✅ Input validation
- ✅ SQL injection prevention
- ✅ Audit logging

### Operations
- ✅ Health checks
- ✅ Graceful shutdown
- ✅ Connection pooling
- ✅ Rate limiting
- ✅ Monitoring endpoints

### Testing
- ✅ Comprehensive test suite
- ✅ Postman collection
- ✅ Health check validation
- ✅ Security testing

## Performance Considerations

### Connection Pooling
- Min: 2 connections (local), scalable for prod
- Max: 10 connections (configurable)
- Increment: 1
- Reuse connections across requests

### Rate Limiting
- Default: 100 requests/hour
- Configurable per environment
- In-memory tracking (scalable with Redis)

### SQL Execution
- Timeout: 300 seconds (configurable)
- Result streaming for large datasets
- Transaction management

### Logging
- Structured JSON logging
- Async file writes
- Log rotation by date
- Minimal performance impact

## Scaling Considerations

### Horizontal Scaling (ECS)
- Stateless application design
- Connection pool per container
- Shared rate limiting (needs Redis)
- Centralized audit logs (S3/CloudWatch)

### Vertical Scaling
- Increase container CPU/memory
- Adjust connection pool size
- Tune worker count

### Database Scaling
- Connection pool optimization
- Query optimization
- Read replicas (if needed)
- Caching layer (Redis)

---

**Version**: 1.0.0
**Last Updated**: February 2024