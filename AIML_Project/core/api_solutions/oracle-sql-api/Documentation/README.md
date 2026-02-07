# Oracle SQL API

A secure, production-ready REST API for executing SQL operations on Oracle databases, with CyberArk integration for credential management and designed for AWS ECS deployment.

## Features

### Core Functionality
- ✅ **SQL Execution**: Execute DQL (SELECT) and DML (INSERT, UPDATE, DELETE, MERGE) operations
- ✅ **File Upload**: Accept and execute SQL files
- ✅ **Connection Pooling**: Efficient Oracle connection management
- ✅ **CyberArk Integration**: Secure credential management for production
- ✅ **API Key Authentication**: Secure API access with JWT token support
- ✅ **Rate Limiting**: Configurable request limits per user/API key
- ✅ **Audit Logging**: Comprehensive audit trail of all operations
- ✅ **Health Monitoring**: Health check and metrics endpoints

### Security Features
- 🔒 API Key authentication with rate limiting
- 🔒 JWT token support for enhanced security
- 🔒 SQL validation to prevent dangerous operations
- 🔒 CyberArk integration for production credentials
- 🔒 Comprehensive audit logging
- 🔒 Input validation and sanitization

### Production Ready
- 🚀 Docker containerization
- 🚀 AWS ECS deployment with Fargate
- 🚀 Health checks and monitoring
- 🚀 Structured logging
- 🚀 Error handling and recovery
- 🚀 Multi-worker Gunicorn deployment

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS + API Key
       ▼
┌─────────────────────┐
│   Load Balancer     │
│  (ALB/API Gateway)  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   ECS Fargate       │
│  Oracle SQL API     │
│  ┌───────────────┐  │
│  │  FastAPI      │  │
│  │  + Gunicorn   │  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │ Connection    │  │
│  │ Pool Manager  │  │
│  └───────┬───────┘  │
└──────────┼──────────┘
           │
    ┌──────▼──────┐
    │  CyberArk   │
    │  (Prod)     │
    └─────────────┘
           │
    ┌──────▼──────┐
    │   Oracle    │
    │  Database   │
    └─────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (for containerization)
- Oracle Database access
- AWS CLI (for ECS deployment)
- CyberArk (for production)

### Local Development

1. **Clone and Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your Oracle credentials
nano .env
```

Required local configuration:
```env
ENVIRONMENT=local
DEBUG=true
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ORCL
ORACLE_USERNAME=your_username
ORACLE_PASSWORD=your_password
SECRET_KEY=your-secret-key
VALID_API_KEYS=your-api-key
```

3. **Run Locally**
```bash
# Start the API
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Test the API**
```bash
# Run test suite
python test_api.py

# Or manually test health endpoint
curl http://localhost:8000/health
```

### Docker Deployment

1. **Build and Run with Docker Compose**
```bash
# Update .env.local with your credentials
nano .env.local

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

2. **Build Docker Image Manually**
```bash
# Build
docker build -t oracle-sql-api:latest .

# Run
docker run -d \
  --name oracle-sql-api \
  -p 8000:8000 \
  --env-file .env.local \
  oracle-sql-api:latest
```

### AWS ECS Deployment

1. **Prerequisites**
- AWS Account with ECS access
- ECR repository created
- ECS cluster configured
- IAM roles setup
- CyberArk configured (production)

2. **Configure Deployment Script**
```bash
# Edit deploy-to-ecs.sh
nano deploy-to-ecs.sh

# Update these values:
# - AWS_ACCOUNT_ID
# - AWS_REGION
# - ECS_CLUSTER
# - ECS_SERVICE
```

3. **Setup AWS Secrets**
```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name oracle-api-secret-key \
  --secret-string "your-secret-key"

aws secretsmanager create-secret \
  --name oracle-api-keys \
  --secret-string "api-key-1,api-key-2"

# CyberArk credentials
aws secretsmanager create-secret \
  --name cyberark-url \
  --secret-string "https://cyberark.example.com"

# ... create other CyberArk secrets
```

4. **Deploy**
```bash
# Make script executable
chmod +x deploy-to-ecs.sh

# Run deployment
./deploy-to-ecs.sh
```

## API Documentation

### Authentication

#### API Key Authentication
Include API key in request header:
```
X-API-Key: your-api-key
```

#### JWT Token (Optional)
1. Generate token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "api_key": "your-api-key"
  }'
```

2. Use token:
```bash
curl -X GET http://localhost:8000/api/v1/pool/status \
  -H "Authorization: Bearer your-token"
```

### Endpoints

#### 1. Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-02-07T10:30:00",
  "version": "1.0.0",
  "environment": "prod",
  "database_status": {
    "status": "healthy",
    "message": "Connection successful"
  },
  "pool_status": {
    "status": "active",
    "open_connections": 5,
    "busy_connections": 2,
    "max_connections": 10
  }
}
```

#### 2. Execute SQL
```bash
POST /api/v1/sql/execute
Content-Type: application/json
X-API-Key: your-api-key

{
  "sql_content": "SELECT * FROM employees WHERE department = 'IT'",
  "username": "john_doe",
  "description": "Get IT department employees"
}
```

Response:
```json
{
  "request_id": "abc-123-def",
  "status": "success",
  "operation_type": "SELECT",
  "rows_affected": 25,
  "data": [
    {"id": 1, "name": "John", "department": "IT"},
    ...
  ],
  "columns": ["id", "name", "department"],
  "execution_time_seconds": 0.234,
  "timestamp": "2024-02-07T10:30:00"
}
```

#### 3. Execute SQL File
```bash
POST /api/v1/sql/execute-file
X-API-Key: your-api-key

Form Data:
- file: test.sql (file upload)
- username: john_doe
- description: Execute monthly report query
```

#### 4. Get Audit Summary
```bash
GET /api/v1/audit/summary?date=20240207
X-API-Key: your-api-key
```

Response:
```json
{
  "date": "20240207",
  "total_requests": 150,
  "successful_requests": 145,
  "failed_requests": 5,
  "operations": {
    "SELECT": 100,
    "INSERT": 30,
    "UPDATE": 15,
    "DELETE": 5
  },
  "unique_users": 12
}
```

#### 5. Rate Limit Status
```bash
GET /api/v1/rate-limit/status
X-API-Key: your-api-key
```

#### 6. Connection Pool Status
```bash
GET /api/v1/pool/status
X-API-Key: your-api-key
```

### Error Responses

```json
{
  "error": "Error message",
  "status_code": 400,
  "timestamp": "2024-02-07T10:30:00"
}
```

Common status codes:
- `400` - Bad Request (invalid SQL, validation failed)
- `401` - Unauthorized (invalid API key)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Environment (local/dev/prod) | local | Yes |
| `DEBUG` | Debug mode | false | No |
| `SECRET_KEY` | JWT secret key | - | Yes |
| `VALID_API_KEYS` | Comma-separated API keys | - | Yes |
| `ORACLE_HOST` | Oracle host | - | Yes (local) |
| `ORACLE_PORT` | Oracle port | 1521 | No |
| `ORACLE_SERVICE_NAME` | Service name | - | Yes (local) |
| `ORACLE_USERNAME` | Username | - | Yes (local) |
| `ORACLE_PASSWORD` | Password | - | Yes (local) |
| `CYBERARK_ENABLED` | Enable CyberArk | false | No |
| `CYBERARK_URL` | CyberArk URL | - | Yes (prod) |
| `RATE_LIMIT_REQUESTS` | Max requests | 100 | No |
| `RATE_LIMIT_PERIOD` | Period in seconds | 3600 | No |

### SQL Operation Restrictions

Allowed operations:
- `SELECT` - Query data
- `INSERT` - Insert data
- `UPDATE` - Update data
- `DELETE` - Delete data
- `MERGE` - Merge operations

Blocked operations:
- `DROP TABLE` - Prevent data loss
- `TRUNCATE` - Prevent data loss
- `ALTER TABLE` - Prevent schema changes
- `CREATE TABLE` - Prevent schema changes
- `GRANT/REVOKE` - Prevent permission changes

## Monitoring and Logging

### Application Logs
- Structured JSON logging
- CloudWatch Logs integration (ECS)
- Log levels: DEBUG, INFO, WARNING, ERROR

### Audit Logs
- All SQL operations logged
- Location: `/app/logs/audit/audit_YYYYMMDD.jsonl`
- Includes: timestamp, user, operation, SQL preview, results

### Metrics
- Request rate
- SQL execution time
- Connection pool utilization
- Error rates

## Security Best Practices

### For Local Development
1. Never commit `.env` files
2. Use strong API keys
3. Rotate keys regularly
4. Limit database permissions

### For Production
1. ✅ Use CyberArk for credentials
2. ✅ Store secrets in AWS Secrets Manager
3. ✅ Enable VPC security groups
4. ✅ Use HTTPS/TLS
5. ✅ Enable CloudWatch monitoring
6. ✅ Regular security audits
7. ✅ Implement least-privilege IAM roles
8. ✅ Enable CloudTrail logging

## Troubleshooting

### Connection Issues
```bash
# Test Oracle connectivity
python -c "import cx_Oracle; print(cx_Oracle.clientversion())"

# Check pool status
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/pool/status
```

### CyberArk Issues
```bash
# Verify CyberArk connectivity
curl -k https://cyberark.example.com/AIMWebService/api/Accounts

# Check logs
docker logs oracle-sql-api | grep -i cyberark
```

### Rate Limiting
```bash
# Check current limits
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/rate-limit/status
```

## Future Enhancements

Based on your requirements, here's the roadmap:

### Phase 2: Monitoring APIs
- [ ] AppDynamics monitoring start/stop API
- [ ] Kibana monitoring start/stop API
- [ ] Unified monitoring control endpoint
- [ ] Monitoring status dashboard

### Phase 3: Additional Features
- [ ] Query result caching
- [ ] Asynchronous execution for long queries
- [ ] Query history and replay
- [ ] Multi-database support
- [ ] Scheduled SQL execution
- [ ] Result export to S3

## Contributing

1. Follow existing code structure
2. Add tests for new features
3. Update documentation
4. Follow PEP 8 style guide

## License

Internal use only - Proprietary

## Support

For issues or questions:
- Check logs: `docker logs oracle-sql-api`
- Review audit logs: `/app/logs/audit/`
- Contact: DevOps Team

---

**Version**: 1.0.0  
**Last Updated**: February 2024