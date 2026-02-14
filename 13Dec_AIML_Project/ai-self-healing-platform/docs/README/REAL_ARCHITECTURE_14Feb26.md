# 🏗️ REAL PRODUCTION ARCHITECTURE GUIDE

## ❌ **WHAT YOU HAVE NOW (Simulated)**

```
test_load.py → Sends fake metrics → Platform receives numbers → "Detects" anomalies
```

**Problem:** No real system impact! Just numbers being sent.

---

## ✅ **WHAT YOU NEED (Real Production)**

```
JMeter → Hits Sample App → App uses CPU/Memory → Real load → 
Prometheus collects metrics → Platform receives REAL metrics → 
Detects REAL anomalies → Triggers K8s HPA → Pods scale automatically
```

**Correct:** Real application creates real resource usage!

---

## 🎯 **THE COMPLETE SYSTEM**

### **Component 1: Sample Application (NEW - You need to build this)**

**Purpose:** Creates REAL system load when hit by JMeter

**File:** `sample_app.py` (Flask application)

**Endpoints:**
- `GET /compute` - CPU intensive (hashing)
- `GET /memory` - Memory intensive (allocates RAM)
- `GET /slow` - High latency (delays)
- `GET /error` - Error generation
- `POST /data` - Mixed load

**What happens:**
```
JMeter hits /compute 1000 times → 
CPU goes from 10% → 80% → 
Prometheus sees high CPU → 
Your platform detects CPU anomaly → 
Triggers K8s HPA to scale pods
```

---

### **Component 2: Prometheus Exporter (Sidecar)**

**Purpose:** Collects REAL metrics from Sample App pods

**What it monitors:**
- CPU usage (from actual computation)
- Memory usage (from actual allocation)
- Response times (from actual requests)
- Error rates (from actual failures)
- Request count (from actual traffic)

**Deployment:**
```yaml
# sample-app pod has Prometheus exporter built-in
# OR use Prometheus node exporter as sidecar
```

---

### **Component 3: Your AI Self-Healing Platform (EXISTING)**

**Purpose:** Monitors metrics, detects anomalies, triggers healing

**Modified to:**
- Pull metrics from Prometheus (not test_load.py)
- Detect REAL anomalies in REAL metrics
- Call Kubernetes API to scale/heal
- Monitor actual HPA behavior

---

### **Component 4: Kubernetes HPA (Auto-scaler)**

**Purpose:** Automatically scales Sample App pods based on load

**Configured to:**
```yaml
minReplicas: 2
maxReplicas: 10
targetCPUUtilizationPercentage: 70
```

When CPU > 70%, HPA scales: 2 pods → 4 pods → 8 pods

---

## 📊 **HOW IT WORKS END-TO-END**

### **Step-by-Step Flow:**

**1. JMeter Sends Load**
```bash
# JMeter Test Plan
Thread Group: 100 users
Ramp-up: 60 seconds
Loop: Infinite

HTTP Requests:
- GET http://sample-app:5000/compute (70%)
- GET http://sample-app:5000/memory (20%)
- GET http://sample-app:5000/slow (10%)
```

**2. Sample App Handles Requests**
```
Sample App Pod receives request to /compute
→ Executes CPU-intensive hashing for 500,000 iterations
→ CPU usage increases from 10% to 85%
→ Takes 2 seconds to complete
→ Returns response to JMeter
```

**3. Prometheus Collects Metrics**
```
Prometheus scrapes Sample App metrics (every 15s):
- container_cpu_usage_seconds_total: 0.85 (85%)
- container_memory_working_set_bytes: 750MB
- http_request_duration_seconds: 2.1s
- http_requests_total: 1523
```

**4. Your Platform Pulls Metrics**
```python
# Your platform queries Prometheus
metrics = prometheus_client.query(
    'container_cpu_usage_seconds_total{pod=~"sample-app-.*"}'
)

# Formats into your metric structure
metric = {
    'timestamp': '2026-02-07T...',
    'cpu_usage': 85.0,  # REAL CPU usage!
    'memory_usage': 75.0,  # REAL memory usage!
    'response_time': 2100,  # REAL latency!
    'error_rate': 0.5,
    'requests_per_sec': 120
}
```

**5. ML Model Detects Anomaly**
```
Your platform's ML model analyzes metric:
→ Detects CPU anomaly (85% > 70% threshold)
→ Severity: CRITICAL
→ Anomaly score: -0.623
```

**6. Self-Healing Orchestrator Acts**
```python
# Your platform decides action
action = decide_action(anomaly)
# action.type = "scale_up"

# Calls Kubernetes API
kubernetes_client.scale_deployment(
    name="sample-app",
    namespace="default",
    replicas=current_replicas + 2
)
```

**7. Kubernetes HPA Scales**
```
K8s HPA detects sustained high CPU
→ Scales Sample App: 2 pods → 4 pods
→ Load distributes across 4 pods
→ CPU per pod drops: 85% → 45%
→ System stabilizes
```

**8. Platform Monitors Recovery**
```
Your platform sees metrics improve:
→ CPU: 85% → 45%
→ Latency: 2100ms → 350ms
→ Marks anomaly as RESOLVED
→ Health score improves: 70% → 95%
```

---

## 🏗️ **DEPLOYMENT ARCHITECTURE**

```
┌─────────────────────────────────────────────────────────────┐
│                   AWS EKS CLUSTER                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  NAMESPACE: applications                             │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────┐                │  │
│  │  │  Sample App Deployment          │                │  │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐       │                │  │
│  │  │  │Pod 1│ │Pod 2│ │Pod 3│  ←HPA │                │  │
│  │  │  └─────┘ └─────┘ └─────┘       │                │  │
│  │  │  Endpoints: /compute, /memory   │                │  │
│  │  └─────────────────────────────────┘                │  │
│  │          ↓ metrics                                   │  │
│  │  ┌─────────────────────────────────┐                │  │
│  │  │  Prometheus (Monitoring)        │                │  │
│  │  │  Scrapes metrics every 15s      │                │  │
│  │  └─────────────────────────────────┘                │  │
│  └──────────────────────────────────────────────────────┘  │
│                     ↓ metrics via HTTP                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  NAMESPACE: platform                                 │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────┐                │  │
│  │  │  AI Platform Deployment         │                │  │
│  │  │  ┌─────┐ ┌─────┐                │                │  │
│  │  │  │Pod 1│ │Pod 2│  ←Your system  │                │  │
│  │  │  └─────┘ └─────┘                │                │  │
│  │  │  • Pulls from Prometheus        │                │  │
│  │  │  • Detects anomalies           │                │  │
│  │  │  • Calls K8s API               │                │  │
│  │  └─────────────────────────────────┘                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Kubernetes HPA Controller                           │  │
│  │  Monitors CPU → Scales Sample App pods               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↑ HTTP requests
                ┌─────────────────────┐
                │  JMeter (Your PC)   │
                │  Sends load to      │
                │  Sample App         │
                └─────────────────────┘
```

---

## 🎯 **WHAT YOU NEED TO DO**

### **Phase 1: Build Sample Application**

**File:** `sample_app.py` (already created above)

**Requirements:**
```txt
Flask==3.0.0
prometheus-flask-exporter==0.23.0
```

**Test locally:**
```powershell
pip install Flask prometheus-flask-exporter
python sample_app.py

# In another terminal
curl http://localhost:5000/compute
# Watch CPU spike!
```

---

### **Phase 2: Modify Your Platform**

**Add Prometheus Integration:**

```python
# In your main.py, add Prometheus client

from prometheus_api_client import PrometheusConnect

# Connect to Prometheus
prom = PrometheusConnect(
    url="http://prometheus-server:9090",
    disable_ssl=True
)

# Pull metrics from Prometheus instead of test_load.py
async def collect_metrics_from_prometheus():
    while True:
        # Query CPU
        cpu_query = 'avg(rate(container_cpu_usage_seconds_total{pod=~"sample-app-.*"}[1m])) * 100'
        cpu_result = prom.custom_query(query=cpu_query)
        
        # Query Memory
        mem_query = '(container_memory_working_set_bytes{pod=~"sample-app-.*"} / container_spec_memory_limit_bytes) * 100'
        mem_result = prom.custom_query(query=mem_query)
        
        # Format into your metric structure
        metric = {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': float(cpu_result[0]['value'][1]),
            'memory_usage': float(mem_result[0]['value'][1]),
            # ... other metrics
        }
        
        # Process like before
        await process_metric(metric)
        
        await asyncio.sleep(15)  # Every 15 seconds
```

---

### **Phase 3: Deploy to Kubernetes**

**Deploy Sample App:**

```yaml
# sample-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
    spec:
      containers:
      - name: app
        image: your-registry/sample-app:latest
        ports:
        - containerPort: 5000
        resources:
          requests:
            cpu: "200m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"

---
apiVersion: v1
kind: Service
metadata:
  name: sample-app
spec:
  selector:
    app: sample-app
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer  # Get external IP for JMeter

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sample-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sample-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Deploy Prometheus:**

```bash
# Using Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus

# Prometheus will auto-discover Sample App pods
```

**Deploy Your Platform:**

```yaml
# ai-platform-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-platform
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: platform
        image: your-registry/ai-platform:v16
        env:
        - name: MODE
          value: "production"
        - name: PROMETHEUS_URL
          value: "http://prometheus-server:9090"
        - name: KUBERNETES_API
          value: "https://kubernetes.default.svc"
```

---

### **Phase 4: Run JMeter Against Sample App**

**JMeter Test Plan:**

```
Thread Group:
  Threads: 100
  Ramp-up: 60s
  Loop: Infinite

HTTP Request 1 (70% of traffic):
  Server: <SAMPLE-APP-EXTERNAL-IP>
  Port: 80
  Path: /compute

HTTP Request 2 (20% of traffic):
  Server: <SAMPLE-APP-EXTERNAL-IP>
  Port: 80
  Path: /memory

HTTP Request 3 (10% of traffic):
  Server: <SAMPLE-APP-EXTERNAL-IP>
  Port: 80
  Path: /slow
```

---

## 📊 **WHAT YOU'LL SEE**

### **1. JMeter Running:**
```
Threads: 100
Samples: 15,234
Errors: 2.3%
Throughput: 234 req/sec
Average response: 1850ms
```

### **2. Sample App Under Load:**
```bash
kubectl top pods

NAME                CPU    MEMORY
sample-app-abc123   85%    380Mi   ← HIGH CPU!
sample-app-def456   82%    360Mi
```

### **3. HPA Scaling:**
```bash
kubectl get hpa

NAME              REFERENCE          TARGETS    MINPODS   MAXPODS   REPLICAS
sample-app-hpa    Deployment/...     85%/70%    2         10        4
                                     ↑
                              CPU above target, scaling!
```

### **4. Your Platform Detecting:**
```
📥 Metric received from Prometheus: CPU=85%, Memory=75%
⚠️  Anomaly detected: CPU_USAGE (severity: critical, score: -0.623)
✅ Action decided: scale_up for CPU_USAGE
🔄 Calling K8s API to scale sample-app deployment
✅ Scaled: 2 → 4 pods
```

### **5. System Recovering:**
```bash
kubectl top pods

NAME                CPU    MEMORY
sample-app-abc123   45%    380Mi   ← CPU dropped!
sample-app-def456   42%    360Mi
sample-app-ghi789   44%    350Mi   ← New pod
sample-app-jkl012   43%    370Mi   ← New pod
```

---

## ✅ **SUMMARY: WHAT'S DIFFERENT**

| Aspect | Current (Simulated) | Real Production |
|--------|---------------------|-----------------|
| **Load Source** | test_load.py sends numbers | JMeter hits real app |
| **Application** | None (just your platform) | Sample app creates real load |
| **CPU Usage** | Fake (just a number) | Real (app actually uses CPU) |
| **Memory Usage** | Fake (just a number) | Real (app allocates memory) |
| **Metrics Source** | POST from test_load.py | Prometheus scrapes real metrics |
| **HPA Trigger** | Manual/simulated | Actual resource usage |
| **Scaling** | Simulated | Real pods scale up/down |
| **Impact** | No real system impact | Real resource management |

---

## 🎯 **YOUR ACTION PLAN**

### **Tomorrow:**

1. **Build Sample App** (1 hour)
   - Deploy `sample_app.py`
   - Test endpoints locally
   - Verify it creates real CPU/memory load

2. **Modify Your Platform** (2 hours)
   - Add Prometheus client
   - Pull metrics from Prometheus
   - Remove test_load.py dependency

3. **Deploy to Minikube** (2 hours)
   - Deploy Sample App with HPA
   - Deploy Prometheus
   - Deploy your AI Platform
   - Verify communication

4. **Test with JMeter** (1 hour)
   - Create test plan
   - Hit Sample App
   - Watch HPA scale
   - Verify your platform detects it

---

## 🎉 **FINAL ARCHITECTURE**

```
JMeter → Sample App (creates real load) → 
Prometheus (collects real metrics) → 
Your AI Platform (detects real anomalies) → 
Kubernetes HPA (real auto-scaling) → 
Presentation: "Real production system!"
```

---

**Does this clarify everything?** This is the **real production architecture** you need! 🚀