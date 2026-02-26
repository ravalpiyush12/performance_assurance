# Oracle SQL API - Multi-Database Platform

Complete implementation of Phase 1 Enhanced with 7 Oracle databases, integrated web UI, and monitoring capabilities.

## 🎯 Features

### Multi-Database Support
- **7 Oracle Databases** with individual authentication
- **CQE_NFT**: Read/Write (DQL + DML) - Direct Auth
- **CD_PTE_READ**: Read-only (DQL) - Direct Auth  
- **CD_PTE_WRITE**: Write (DML) - CyberArk
- **CAS_PTE_READ**: Read-only (DQL) - Direct Auth
- **CAS_PTE_WRITE**: Write (DML) - CyberArk
- **PORTAL_PTE_READ**: Read-only (DQL) - Direct Auth
- **PORTAL_PTE_WRITE**: Write (DML) - CyberArk

### Security Features
- Database-specific API keys and secret keys
- CyberArk integration for WRITE databases
- SQL operation validation (DQL/DML enforcement)
- JWT token support
- Rate limiting
- Audit logging (JSONL format)

### Web UI
- Tab-based interface
- Oracle SQL execution with database selector
- AppDynamics monitoring
- Kibana/Elasticsearch monitoring  
- Splunk monitoring
- MongoDB analysis
- Live API testing
- Interactive documentation

## 📁 Project Structure

```
oracle-sql-api/
├── app/
│   ├── main.py                          # Main FastAPI application
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                  # Multi-database settings
│   │   └── database_config.py           # Database configurations
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py                  # Security manager
│   │   └── sql_validator.py             # SQL validation
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection_manager.py        # Connection pool manager
│   │   ├── oracle_handler.py            # Oracle connections
│   │   └── sql_executor.py              # SQL execution
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── audit.py                     # Audit logging
│   │   └── cyberark.py                  # CyberArk client
│   └── templates/
│       └── index.html                   # Web UI
├── config/
│   └── .env.local.example               # Configuration example
├── kubernetes/
│   ├── values.yaml                      # Helm values
│   ├── deployment.yaml                  # Kubernetes deployment
│   └── secrets.yaml.example             # Secrets template
├── requirements.txt
├── Dockerfile
├── gunicorn.conf.py
└── README.md
```

## 🚀 Quick Start

### Local Development

1. **Clone and setup**
```bash
git clone <your-repo>
cd oracle-sql-api
```

2. **Create environment**
```bash
cp config/.env.local.example .env.local
# Edit .env.local with your database credentials
```

3. **Generate secure keys**
```bash
# Generate SECRET_KEY for each database
for db in CQE_NFT CD_PTE_READ CD_PTE_WRITE CAS_PTE_READ CAS_PTE_WRITE PORTAL_PTE_READ PORTAL_PTE_WRITE; do
  echo "${db}_SECRET_KEY=$(openssl rand -hex 32)"
done

# Generate API_KEYS for each database
for db in CQE_NFT CD_PTE_READ CD_PTE_WRITE CAS_PTE_READ CAS_PTE_WRITE PORTAL_PTE_READ PORTAL_PTE_WRITE; do
  echo "${db}_API_KEYS=apk_live_$(openssl rand -hex 20),apk_live_$(openssl rand -hex 20)"
done
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Run application**
```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn -c gunicorn.conf.py main:app
```

6. **Access UI**
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

### Docker Deployment

1. **Build image**
```bash
docker build -t oracle-sql-api:2.0.0 .
```

2. **Run container**
```bash
docker run -d \
  --name oracle-sql-api \
  -p 8000:8000 \
  --env-file .env.local \
  oracle-sql-api:2.0.0
```

### Kubernetes/OpenShift Deployment

1. **Create secrets**
```bash
# Create secret for database credentials
kubectl create secret generic oracle-db-secrets \
  --from-literal=cqe-nft-password='your-password' \
  --from-literal=cqe-nft-secret-key='your-secret-key' \
  --from-literal=cqe-nft-api-keys='key1,key2' \
  --from-literal=cd-pte-read-password='your-password' \
  --from-literal=cd-pte-read-secret-key='your-secret-key' \
  --from-literal=cd-pte-read-api-keys='key1,key2' \
  # ... repeat for all databases
```

2. **Update values.yaml**
```bash
# Edit kubernetes/values.yaml with your environment details
vim kubernetes/values.yaml
```

3. **Deploy with Helm**
```bash
helm install oracle-sql-api ./kubernetes \
  -f kubernetes/values.yaml \
  -n your-namespace
```

4. **Or deploy directly**
```bash
kubectl apply -f kubernetes/deployment.yaml -n your-namespace
```

## 📖 API Documentation

### Database-Specific Endpoints

Each database has its own set of endpoints:

#### Execute SQL Query
```bash
POST /api/v1/{database}/execute
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json

Body:
{
  "sql": "SELECT * FROM users WHERE status = :status",
  "params": {"status": "active"},
  "fetch_size": 1000
}
```

#### Execute SQL File
```bash
POST /api/v1/{database}/execute-file
Headers:
  X-API-Key: your-api-key
  Content-Type: multipart/form-data

Body:
  file: your-sql-file.sql
```

#### Database Health Check
```bash
GET /api/v1/{database}/health
Headers:
  X-API-Key: your-api-key
```

### Global Endpoints

#### List All Databases
```bash
GET /api/v1/databases
```

#### Global Health Check
```bash
GET /health
```

## 🔒 Security

### API Keys
Each database requires its own API key:
```bash
X-API-Key: apk_live_your_database_specific_key_here
```

### SQL Validation
- **READ databases (DQL only)**: Only SELECT statements allowed
- **WRITE databases (DML only)**: INSERT, UPDATE, DELETE allowed
- **CQE_NFT (DQL + DML)**: Both SELECT and DML allowed
- **Always blocked**: DROP, TRUNCATE, CREATE, ALTER, GRANT, REVOKE

### CyberArk Integration
WRITE databases automatically retrieve credentials from CyberArk:
```yaml
cyberark:
  enabled: "true"
  url: "https://cyberark.example.com/AIMWebService/api/Accounts"
  appId: "OracleSQLAPI"
```

## 🎨 Web UI Usage

1. **Access UI**: Navigate to http://your-domain.com
2. **Select database**: Choose from dropdown (CQE_NFT, CD_PTE_READ, etc.)
3. **Enter API key**: Your database-specific API key
4. **Write SQL**: Enter your query
5. **Execute**: Click "Execute Query" or upload SQL file
6. **View results**: See formatted JSON response

### Monitoring Tabs
- **AppDynamics**: Monitor applications and metrics
- **Kibana**: Search and analyze Elasticsearch logs
- **Splunk**: Run Splunk queries
- **MongoDB**: Analyze collections and performance

## 📊 Monitoring

### Audit Logs
All SQL executions are logged to JSONL format:
```json
{
  "timestamp": "2024-02-13T10:30:00",
  "event_type": "sql_executed",
  "database": "CQE_NFT",
  "sql": "SELECT * FROM users",
  "rows_affected": 100,
  "execution_time_ms": 45.2,
  "api_key": "***key***"
}
```

Location: `/app/logs/audit/audit_YYYYMMDD.jsonl`

### Health Monitoring
```bash
# Check all databases
curl http://localhost:8000/health

# Check specific database
curl -H "X-API-Key: your-key" \
  http://localhost:8000/api/v1/CQE_NFT/health
```

## 🛠️ Configuration

### Environment Variables

Each database requires these variables:
```bash
# Example for CQE_NFT
CQE_NFT_HOST=db.example.com
CQE_NFT_PORT=1521
CQE_NFT_SERVICE_NAME=ORCL
CQE_NFT_USERNAME=user
CQE_NFT_PASSWORD=pass
CQE_NFT_POOL_MIN=2
CQE_NFT_POOL_MAX=10
CQE_NFT_SECRET_KEY=64-char-hex-string
CQE_NFT_API_KEYS=key1,key2,key3
```

### Kubernetes Secrets

Store sensitive data in Kubernetes secrets:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: oracle-db-secrets
type: Opaque
stringData:
  cqe-nft-password: "your-password"
  cqe-nft-secret-key: "your-secret-key"
  cqe-nft-api-keys: "key1,key2"
```

## 📝 Requirements

### Python Dependencies
```
fastapi==0.88.0
pydantic==1.10.18
uvicorn[standard]==0.27.0
gunicorn==21.2.0
cx_Oracle==8.3.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
requests==2.31.0
pymongo==4.6.1
python-dotenv==1.0.0
aiofiles==23.2.1
```

### System Requirements
- Python 3.11+
- Oracle Instant Client 21.15
- 2GB RAM minimum (4GB recommended)
- 10GB disk space

## 🐛 Troubleshooting

### Connection Issues
```bash
# Test Oracle connectivity from pod
kubectl exec -it <pod> -- bash
nc -zv oracle-host 1521

# Check environment variables
kubectl exec <pod> -- env | grep CQE_NFT

# View logs
kubectl logs -f <pod>
```

### API Key Issues
- Ensure API key matches database-specific key
- Check header: `X-API-Key` (case-sensitive)
- Verify key in Kubernetes secret

### SQL Validation Errors
- Check allowed operations for database
- READ databases: SELECT only
- WRITE databases: INSERT/UPDATE/DELETE only
- CQE_NFT: Both allowed

## 📞 Support

For issues or questions:
1. Check logs: `kubectl logs <pod>`
2. Review health endpoint: `/health`
3. Check API docs: `/api/docs`

## 📄 License

Proprietary - Internal Use Only

---

**Version**: 2.0.0  
**Last Updated**: February 2026  
**Author**: DevOps Team