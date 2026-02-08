# Monitoring API Documentation - Phase 2

## 🎯 Overview

The Oracle SQL API now includes comprehensive monitoring capabilities for:
- **AppDynamics** - Application performance monitoring
- **Kibana/Elasticsearch** - Log aggregation and analysis
- **Splunk** - Enterprise log management
- **MongoDB** - Database collection analysis

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Unified Control API](#unified-control-api)
4. [AppDynamics API](#appdynamics-api)
5. [Kibana API](#kibana-api)
6. [Splunk API](#splunk-api)
7. [MongoDB API](#mongodb-api)
8. [Dashboard](#dashboard)
9. [Examples](#examples)

---

## 🚀 Quick Start

### 1. Enable Monitoring Systems

Edit your `.env` file:

```env
# Enable the monitoring systems you need
APPDYNAMICS_ENABLED=true
KIBANA_ENABLED=true
SPLUNK_ENABLED=true
MONGODB_ENABLED=true

# Configure credentials (see Configuration section)
```

### 2. Start Monitoring

```bash
# Start all monitoring systems
curl -X POST http://localhost:8000/api/v1/monitoring/start \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"system": "all", "parameters": {}}'

# Start specific system
curl -X POST http://localhost:8000/api/v1/monitoring/start \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "system": "kibana",
    "parameters": {
      "time_range_minutes": 60,
      "log_level": "ERROR"
    }
  }'
```

### 3. Check Status

```bash
curl -X GET http://localhost:8000/api/v1/monitoring/status \
  -H "X-API-Key: your-api-key"
```

### 4. View Dashboard

```bash
curl -X GET http://localhost:8000/api/v1/monitoring/dashboard \
  -H "X-API-Key: your-api-key"
```

---

## ⚙️ Configuration

### AppDynamics Configuration

```env
APPDYNAMICS_ENABLED=true
APPDYNAMICS_CONTROLLER_URL=https://your-controller.saas.appdynamics.com
APPDYNAMICS_ACCOUNT_NAME=your_account
APPDYNAMICS_USERNAME=your_username@your_account
APPDYNAMICS_PASSWORD=your_password
APPDYNAMICS_APPLICATION_NAME=MyApplication
APPDYNAMICS_TIMEOUT=30
```

**Required Access:**
- AppDynamics Controller access
- API permissions for metrics and business transactions

### Kibana/Elasticsearch Configuration

```env
KIBANA_ENABLED=true
KIBANA_URL=https://your-kibana.example.com
ELASTICSEARCH_URL=https://your-elasticsearch.example.com
KIBANA_USERNAME=elastic
KIBANA_PASSWORD=your_password
KIBANA_INDEX_PATTERN=logstash-*
KIBANA_TIMEOUT=30
```

**Required Access:**
- Elasticsearch read access
- Kibana API access

### Splunk Configuration

```env
SPLUNK_ENABLED=true
SPLUNK_URL=https://your-splunk.example.com:8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=your_password
SPLUNK_INDEX=main
SPLUNK_TIMEOUT=30
```

**Required Access:**
- Splunk REST API access
- Search permissions

### MongoDB Configuration

```env
MONGODB_ENABLED=true
MONGODB_CONNECTION_STRING=mongodb://username:password@localhost:27017/
MONGODB_DATABASE=admin
MONGODB_TIMEOUT=10
MONGODB_MAX_POOL_SIZE=10
```

**Required Access:**
- MongoDB read access
- Database profiling (for slow queries)

---

## 🎛️ Unified Control API

### Start Monitoring

**Endpoint:** `POST /api/v1/monitoring/start`

**Request Body:**
```json
{
  "system": "appdynamics|kibana|splunk|mongodb|all",
  "parameters": {
    // System-specific parameters
  }
}
```

**System-Specific Parameters:**

#### AppDynamics
```json
{
  "system": "appdynamics",
  "parameters": {
    "application_name": "MyApp",
    "tier_name": "WebTier",  // optional
    "node_name": "Node1",    // optional
    "duration_minutes": 60
  }
}
```

#### Kibana
```json
{
  "system": "kibana",
  "parameters": {
    "index_pattern": "logs-*",
    "time_range_minutes": 60,
    "query": "status:500",     // optional
    "log_level": "ERROR"       // optional
  }
}
```

#### Splunk
```json
{
  "system": "splunk",
  "parameters": {
    "index": "main",
    "sourcetype": "access_combined",  // optional
    "search_query": "error OR fail",  // optional
    "time_range_minutes": 60
  }
}
```

#### MongoDB
```json
{
  "system": "mongodb",
  "parameters": {
    "database_name": "mydb",
    "collections": ["users", "orders"],  // optional, null = all
    "analysis_interval_minutes": 60
  }
}
```

**Response:**
```json
{
  "status": "success",
  "system": "kibana",
  "result": {
    "status": "started",
    "index_pattern": "logs-*",
    "start_time": "2024-02-07T10:00:00",
    "end_time": "2024-02-07T11:00:00",
    "initial_log_count": 15420,
    "monitoring_active": true
  },
  "timestamp": "2024-02-07T10:00:00"
}
```

### Stop Monitoring

**Endpoint:** `POST /api/v1/monitoring/stop`

**Request Body:**
```json
{
  "system": "appdynamics|kibana|splunk|mongodb|all"
}
```

**Response:**
```json
{
  "status": "success",
  "system": "kibana",
  "result": {
    "status": "stopped",
    "stop_time": "2024-02-07T11:00:00",
    "duration_minutes": 60.0,
    "final_log_count": 16240,
    "monitoring_active": false
  },
  "timestamp": "2024-02-07T11:00:00"
}
```

### Get Status

**Endpoint:** `GET /api/v1/monitoring/status?system={system}`

**Parameters:**
- `system` (optional): Specific system or omit for all

**Response (All Systems):**
```json
{
  "overall_status": "active",
  "systems": {
    "appdynamics": {
      "status": "running",
      "details": {
        "monitoring_active": true,
        "last_fetch_time": "2024-02-07T10:30:00",
        "application": "MyApp"
      }
    },
    "kibana": {
      "status": "stopped",
      "details": {
        "monitoring_active": false
      }
    },
    "splunk": {
      "status": "not_configured"
    },
    "mongodb": {
      "status": "running",
      "details": {
        "monitoring_active": true,
        "database": "mydb"
      }
    }
  },
  "timestamp": "2024-02-07T10:30:00"
}
```

### Get Dashboard

**Endpoint:** `GET /api/v1/monitoring/dashboard`

**Response:**
```json
{
  "timestamp": "2024-02-07T10:30:00",
  "overall_status": "active",
  "systems_count": {
    "total": 4,
    "configured": 3,
    "running": 2,
    "stopped": 1,
    "error": 0,
    "not_configured": 1
  },
  "systems": {
    "appdynamics": {
      "status": "running",
      "enabled": true,
      "details": {...},
      "health": {
        "status": "healthy"
      }
    },
    // ... other systems
  }
}
```

---

## 📊 AppDynamics API

### Fetch Metrics

**Endpoint:** `GET /api/v1/monitoring/appdynamics/metrics`

**Parameters:**
- `metric_path`: Metric path (default: "Overall Application Performance|*")
- `time_range_minutes`: Time range (default: 15)

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/appdynamics/metrics?\
metric_path=Overall%20Application%20Performance|Average%20Response%20Time%20(ms)\
&time_range_minutes=30" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "status": "success",
  "application": "MyApp",
  "metric_path": "Overall Application Performance|Average Response Time (ms)",
  "time_range_minutes": 30,
  "metrics_count": 30,
  "metrics": [
    {
      "metricName": "BTM|Application Summary|Average Response Time (ms)",
      "metricPath": "Overall Application Performance|...",
      "frequency": "ONE_MIN",
      "metricValues": [
        {
          "startTimeInMillis": 1707307200000,
          "value": 245,
          "min": 210,
          "max": 320,
          "current": 245,
          "sum": 245,
          "count": 1,
          "standardDeviation": 0,
          "occurrences": 1
        }
      ]
    }
  ],
  "fetched_at": "2024-02-07T10:30:00"
}
```

### Get Business Transactions

**Endpoint:** `GET /api/v1/monitoring/appdynamics/business-transactions`

**Example:**
```bash
curl -X GET http://localhost:8000/api/v1/monitoring/appdynamics/business-transactions \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "status": "success",
  "application": "MyApp",
  "transaction_count": 25,
  "transactions": [
    {
      "name": "/api/users",
      "id": 123,
      "entryPointType": "SERVLET",
      "tierName": "WebTier",
      "background": false
    }
  ],
  "fetched_at": "2024-02-07T10:30:00"
}
```

---

## 📝 Kibana API

### Fetch Logs

**Endpoint:** `GET /api/v1/monitoring/kibana/logs`

**Parameters:**
- `time_range_minutes`: Time range (default: 15)
- `size`: Number of logs (default: 100)
- `log_level`: Filter by level (optional)

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/kibana/logs?\
time_range_minutes=30&size=50&log_level=ERROR" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "status": "success",
  "index_pattern": "logstash-*",
  "time_range_minutes": 30,
  "total_hits": 1523,
  "returned_logs": 50,
  "logs": [
    {
      "@timestamp": "2024-02-07T10:30:00.000Z",
      "level": "ERROR",
      "message": "Connection timeout",
      "service": "api-gateway",
      "_id": "abc123",
      "_index": "logstash-2024.02.07"
    }
  ],
  "fetched_at": "2024-02-07T10:30:00"
}
```

### Search Errors

**Endpoint:** `GET /api/v1/monitoring/kibana/errors`

**Parameters:**
- `time_range_minutes`: Time range (default: 60)
- `size`: Number of errors (default: 50)

### Get Statistics

**Endpoint:** `GET /api/v1/monitoring/kibana/statistics`

**Response:**
```json
{
  "status": "success",
  "total_logs": 45230,
  "log_levels": {
    "ERROR": 1523,
    "WARN": 3241,
    "INFO": 38456,
    "DEBUG": 2010
  },
  "timeline": [
    {
      "timestamp": "2024-02-07T10:00:00",
      "count": 752
    }
  ]
}
```

---

## 🔍 Splunk API

### Search Events

**Endpoint:** `POST /api/v1/monitoring/splunk/search`

**Parameters:**
- `search_query`: SPL query
- `earliest_time`: Start time (default: "-15m")
- `latest_time`: End time (default: "now")
- `max_results`: Max results (default: 100)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/splunk/search?\
search_query=index=main%20error\
&earliest_time=-1h\
&max_results=50" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "status": "success",
  "search_query": "index=main error",
  "search_id": "1707307200.123",
  "event_count": 45,
  "events": [
    {
      "_time": "2024-02-07 10:30:00",
      "_raw": "ERROR: Database connection failed",
      "host": "web-server-01",
      "source": "/var/log/app.log",
      "sourcetype": "app_logs"
    }
  ],
  "fetched_at": "2024-02-07T10:30:00"
}
```

### Search Errors

**Endpoint:** `GET /api/v1/monitoring/splunk/errors`

### Get Statistics

**Endpoint:** `GET /api/v1/monitoring/splunk/statistics`

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_events": 125430,
    "by_sourcetype": {
      "access_logs": 98234,
      "app_logs": 25196,
      "system_logs": 2000
    },
    "by_host": {
      "web-server-01": 62715,
      "web-server-02": 62715
    }
  }
}
```

---

## 🗄️ MongoDB API

### Analyze Collection

**Endpoint:** `GET /api/v1/monitoring/mongodb/collection/{collection_name}`

**Parameters:**
- `collection_name`: Collection name (path)
- `sample_size`: Sample size (default: 1000)

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/mongodb/collection/users?\
sample_size=500" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "status": "success",
  "collection": "users",
  "document_count": 125430,
  "size_info": {
    "count": 125430,
    "size_mb": 2456.78,
    "avg_obj_size": 2048,
    "storage_size_mb": 2800.45,
    "total_index_size_mb": 345.12
  },
  "indexes_count": 5,
  "indexes": [
    {
      "name": "_id_",
      "key": {"_id": 1}
    },
    {
      "name": "email_1",
      "key": {"email": 1}
    }
  ],
  "schema_analysis": {
    "field_count": 15,
    "fields": {
      "email": {
        "types": ["str"],
        "null_count": 0,
        "null_percentage": 0.0
      },
      "age": {
        "types": ["int", "NoneType"],
        "null_count": 125,
        "null_percentage": 10.0
      }
    }
  },
  "analyzed_at": "2024-02-07T10:30:00"
}
```

### Analyze All Collections

**Endpoint:** `GET /api/v1/monitoring/mongodb/collections`

**Response:**
```json
{
  "status": "success",
  "database": "mydb",
  "collections_count": 15,
  "total_documents": 545230,
  "total_size_mb": 12456.78,
  "collections_analysis": [
    {
      "collection": "users",
      "document_count": 125430,
      "size_info": {...}
    }
  ]
}
```

### Get Slow Queries

**Endpoint:** `GET /api/v1/monitoring/mongodb/slow-queries`

**Parameters:**
- `threshold_ms`: Threshold in ms (default: 100)
- `limit`: Max results (default: 50)

**Response:**
```json
{
  "status": "success",
  "slow_queries_count": 15,
  "slow_queries": [
    {
      "timestamp": "2024-02-07T10:30:00",
      "duration_ms": 2450,
      "operation": "query",
      "namespace": "mydb.users",
      "command": "{find: 'users', filter: {...}}"
    }
  ]
}
```

### Get Database Statistics

**Endpoint:** `GET /api/v1/monitoring/mongodb/statistics`

---

## 📈 Dashboard

The dashboard endpoint provides a comprehensive view of all monitoring systems:

```bash
curl -X GET http://localhost:8000/api/v1/monitoring/dashboard \
  -H "X-API-Key: your-api-key"
```

Use this to build monitoring dashboards or status pages.

---

## 💡 Examples

### Example 1: Start All Monitoring

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/monitoring/start",
    headers={"X-API-Key": "your-api-key"},
    json={
        "system": "all",
        "parameters": {}
    }
)

print(response.json())
```

### Example 2: Monitor Errors Across All Systems

```python
import requests

api_key = "your-api-key"
base_url = "http://localhost:8000/api/v1/monitoring"

# Start monitoring
requests.post(f"{base_url}/start", 
    headers={"X-API-Key": api_key},
    json={"system": "all", "parameters": {}})

# Fetch errors from each system
kibana_errors = requests.get(f"{base_url}/kibana/errors", 
    headers={"X-API-Key": api_key}).json()

splunk_errors = requests.get(f"{base_url}/splunk/errors",
    headers={"X-API-Key": api_key}).json()

# Analyze results
print(f"Kibana errors: {kibana_errors['returned_logs']}")
print(f"Splunk errors: {splunk_errors['event_count']}")
```

### Example 3: MongoDB Health Check

```python
import requests

api_key = "your-api-key"
base_url = "http://localhost:8000/api/v1/monitoring/mongodb"

# Get statistics
stats = requests.get(f"{base_url}/statistics",
    headers={"X-API-Key": api_key}).json()

# Check slow queries
slow_queries = requests.get(f"{base_url}/slow-queries?threshold_ms=200",
    headers={"X-API-Key": api_key}).json()

# Analyze critical collection
users_analysis = requests.get(f"{base_url}/collection/users",
    headers={"X-API-Key": api_key}).json()

print(f"Database size: {stats['total_size_mb']} MB")
print(f"Slow queries: {slow_queries['slow_queries_count']}")
print(f"Users collection: {users_analysis['document_count']} documents")
```

---

## 🔒 Security

All monitoring endpoints require API key authentication:

```
X-API-Key: your-api-key
```

All monitoring operations are audit logged for compliance.

---

## 🐛 Troubleshooting

### Connection Issues

```bash
# Check monitoring status
curl -X GET http://localhost:8000/api/v1/monitoring/status \
  -H "X-API-Key: your-api-key"

# Check specific system
curl -X GET "http://localhost:8000/api/v1/monitoring/status?system=kibana" \
  -H "X-API-Key: your-api-key"
```

### Configuration Issues

1. Verify credentials in `.env`
2. Check network connectivity
3. Review logs: `docker logs oracle-sql-api`

---

## 📚 Additional Resources

- [AppDynamics REST API Documentation](https://docs.appdynamics.com/appd/23.x/latest/en/extend-appdynamics/appdynamics-apis)
- [Elasticsearch REST API](https://www.elastic.co/guide/en/elasticsearch/reference/current/rest-apis.html)
- [Splunk REST API](https://docs.splunk.com/Documentation/Splunk/latest/RESTREF/RESTprolog)
- [MongoDB Manual](https://www.mongodb.com/docs/manual/)

---

**Version**: 2.0.0  
**Last Updated**: February 2024