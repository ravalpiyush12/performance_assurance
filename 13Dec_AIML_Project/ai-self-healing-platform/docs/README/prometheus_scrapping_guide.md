# 🎯 PROMETHEUS SCRAPING CONFIGURATION GUIDE

Complete guide to configure Prometheus to scrape metrics from your sample-app.

---

## ❓ **YOUR QUESTION ANSWERED**

> "Will Prometheus configuration be part of deployment or do I need other steps?"

**ANSWER:** You need **BOTH**:

1. ✅ **Sample App Deployment** - with Prometheus annotations
2. ✅ **Prometheus Configuration** - to actually scrape

**It's NOT automatic!** Here's how to set it up properly.

---

## 📋 **WHAT YOU NEED**

### **Component 1: Sample App with /metrics Endpoint**

**File:** `sample_app_with_prometheus.py` (already created)

**Key Features:**
```python
# Exposes metrics at /metrics endpoint
from prometheus_client import Counter, Histogram, Gauge

# Automatic metrics
REQUEST_COUNT = Counter('http_requests_total', ...)
REQUEST_DURATION = Histogram('http_request_duration_seconds', ...)

# Custom metrics
CPU_USAGE = Gauge('app_cpu_usage_percent', ...)
MEMORY_USAGE = Gauge('app_memory_usage_bytes', ...)
```

**Test locally:**
```powershell
# Install dependencies
pip install Flask prometheus-client psutil

# Run app
python sample_app_with_prometheus.py

# Check metrics endpoint
curl http://localhost:5000/metrics
```

**Should return:**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="health",method="GET",status="200"} 1.0

# HELP app_cpu_usage_percent Current CPU usage percentage
# TYPE app_cpu_usage_percent gauge
app_cpu_usage_percent 15.3

# HELP app_memory_usage_bytes Current memory usage in bytes
# TYPE app_memory_usage_bytes gauge
app_memory_usage_bytes 45678900.0
```

---

### **Component 2: Kubernetes Deployment with Annotations**

**File:** `kubernetes-sample-app.yaml`

**CRITICAL ANNOTATIONS:**
```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"       # ← Enable scraping
    prometheus.io/port: "5000"         # ← Port to scrape
    prometheus.io/path: "/metrics"     # ← Metrics path
```

**These annotations tell Prometheus:**
- ✅ "Yes, scrape this pod"
- ✅ "Scrape on port 5000"
- ✅ "Metrics are at /metrics endpoint"

---

### **Component 3: Prometheus Configuration**

**Two Methods:**

#### **Method A: Using Helm (Recommended)**

**Step 1: Install Prometheus with auto-discovery**
```bash
# Add Prometheus repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install with default config (auto-discovers annotated pods)
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring-demo \
  --create-namespace
```

**Prometheus automatically discovers pods with `prometheus.io/scrape: "true"`**

#### **Method B: Manual Configuration**

Create `prometheus-config.yaml`:
```yaml
scrape_configs:
- job_name: 'kubernetes-pods'
  kubernetes_sd_configs:
  - role: pod
  
  relabel_configs:
  # Keep only pods with prometheus.io/scrape = true
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    action: keep
    regex: true
```

---

## 🚀 **COMPLETE DEPLOYMENT STEPS**

### **STEP 1: Prepare Sample App**

**1.1: Create Docker image**
```bash
# Create Dockerfile
cat > Dockerfile.sampleapp << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir Flask prometheus-client psutil

# Copy app
COPY sample_app_with_prometheus.py app.py

# Expose port
EXPOSE 5000

# Run app
CMD ["python", "app.py"]
EOF

# Build image
docker build -f Dockerfile.sampleapp -t sample-app:latest .
```

**1.2: Load into Minikube (if testing locally)**
```bash
minikube image load sample-app:latest
```

---

### **STEP 2: Deploy Prometheus**

**2.1: Install via Helm**
```bash
# Install Prometheus
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring-demo \
  --create-namespace \
  --set server.service.type=NodePort \
  --set server.service.nodePort=30090

# Wait for pods
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring-demo --timeout=300s

# Get Prometheus URL
minikube service prometheus-server -n monitoring-demo --url
```

**Expected output:**
```
http://192.168.49.2:30090
```

**2.2: Verify Prometheus is running**
```bash
# Check pods
kubectl get pods -n monitoring-demo

# Should show:
# prometheus-server-xxx    Running
# prometheus-alertmanager-xxx    Running
```

---

### **STEP 3: Deploy Sample App**

```bash
# Deploy sample app
kubectl apply -f kubernetes-sample-app.yaml

# Wait for pods
kubectl wait --for=condition=ready pod -l app=sample-app -n monitoring-demo --timeout=300s

# Check pods
kubectl get pods -n monitoring-demo

# Should show:
# sample-app-xxx    Running
# sample-app-yyy    Running
```

---

### **STEP 4: Verify Prometheus is Scraping**

**4.1: Open Prometheus UI**
```bash
# Get URL
minikube service prometheus-server -n monitoring-demo --url

# Open in browser
start http://192.168.49.2:30090
```

**4.2: Check Targets**
1. Go to: **Status → Targets**
2. Look for: `kubernetes-pods` job
3. Should see: `sample-app-xxx` pods with **State: UP**

**Screenshot what you should see:**
```
Endpoint                               State    Last Scrape
sample-app-abc123:5000/metrics         UP       2.5s ago
sample-app-def456:5000/metrics         UP       1.8s ago
```

**4.3: Query Metrics**

Go to **Graph** tab and try these queries:

**Query 1: Check app is being scraped**
```promql
up{job="kubernetes-pods", app="sample-app"}
```
**Expected:** Value = 1 (means UP)

**Query 2: HTTP request count**
```promql
http_requests_total{app="sample-app"}
```
**Expected:** Shows request counters

**Query 3: CPU usage**
```promql
app_cpu_usage_percent{app="sample-app"}
```
**Expected:** Shows CPU percentage (e.g., 15.3)

**Query 4: Memory usage**
```promql
app_memory_usage_bytes{app="sample-app"}
```
**Expected:** Shows memory in bytes

---

### **STEP 5: Test End-to-End**

**5.1: Hit sample app to generate metrics**
```bash
# Get sample-app URL
minikube service sample-app -n monitoring-demo --url

# Hit /compute endpoint 10 times
for i in {1..10}; do
  curl http://192.168.49.2:30080/compute
  sleep 1
done
```

**5.2: Check Prometheus shows increased metrics**
```promql
# Request count should increase
http_requests_total{app="sample-app", endpoint="compute"}

# CPU should spike
app_cpu_usage_percent{app="sample-app"}
```

**5.3: Verify in your AI Platform**

Your AI platform queries Prometheus:
```python
# In main_v17.py
cpu_query = 'avg(app_cpu_usage_percent{app="sample-app"})'
cpu_result = prometheus_client.custom_query(query=cpu_query)
```

---

## 🔍 **TROUBLESHOOTING**

### **Issue 1: Prometheus not discovering sample-app**

**Check:**
```bash
# 1. Verify annotations on pod
kubectl get pod -n monitoring-demo -l app=sample-app -o yaml | grep -A 5 annotations

# Should show:
# annotations:
#   prometheus.io/scrape: "true"
#   prometheus.io/port: "5000"
#   prometheus.io/path: "/metrics"
```

**If missing, redeploy:**
```bash
kubectl delete -f kubernetes-sample-app.yaml
kubectl apply -f kubernetes-sample-app.yaml
```

---

### **Issue 2: Targets show as DOWN**

**Check:**
```bash
# 1. Can you access /metrics from inside cluster?
kubectl exec -it deployment/prometheus-server -n monitoring-demo -- \
  wget -qO- http://sample-app.monitoring-demo.svc.cluster.local:5000/metrics

# Should return Prometheus metrics
```

**If fails:**
```bash
# Check sample-app is actually running
kubectl logs deployment/sample-app -n monitoring-demo

# Should show: "Starting Sample Application on port 5000"
```

---

### **Issue 3: Metrics endpoint returns 404**

**Check:**
```bash
# Test /metrics endpoint directly
curl http://<SAMPLE-APP-IP>:5000/metrics

# If 404, app might not have Prometheus client installed
```

**Fix:**
```bash
# Rebuild Docker image with prometheus-client
pip install prometheus-client
```

---

## ✅ **VERIFICATION CHECKLIST**

After complete setup:

- [ ] Sample app exposes `/metrics` endpoint
- [ ] Kubernetes deployment has Prometheus annotations
- [ ] Prometheus pod is running
- [ ] Prometheus UI accessible
- [ ] Sample app pods show in Prometheus Targets (State: UP)
- [ ] Can query `app_cpu_usage_percent` in Prometheus
- [ ] Can query `http_requests_total` in Prometheus
- [ ] Your AI platform can query Prometheus successfully

---

## 📊 **PROMETHEUS QUERIES YOUR AI PLATFORM WILL USE**

These are the queries from `main_v17.py`:

```python
# CPU usage
'avg(app_cpu_usage_percent{app="sample-app"})'

# Memory usage  
'avg(app_memory_usage_percent{app="sample-app"})'

# Response time (average)
'avg(rate(http_request_duration_seconds_sum{app="sample-app"}[1m]) / rate(http_request_duration_seconds_count{app="sample-app"}[1m])) * 1000'

# Error rate
'sum(rate(app_errors_total{app="sample-app"}[1m])) / sum(rate(http_requests_total{app="sample-app"}[1m])) * 100'

# Request rate
'sum(rate(http_requests_total{app="sample-app"}[1m]))'
```

---

## 🎯 **SUMMARY**

**The Flow:**

1. **Sample App** exposes metrics at `/metrics`
2. **Kubernetes Deployment** has annotations telling Prometheus to scrape
3. **Prometheus** discovers pods automatically via Kubernetes API
4. **Prometheus** scrapes `/metrics` every 15 seconds
5. **Prometheus** stores time-series data
6. **Your AI Platform** queries Prometheus for metrics
7. **ML Model** detects anomalies in REAL metrics
8. **Self-Healing** triggers K8s scaling

**All automatic once configured!** 🎉

---

**Files you need:**
1. ✅ `sample_app_with_prometheus.py` - App with metrics
2. ✅ `kubernetes-sample-app.yaml` - Deployment with annotations
3. ✅ `prometheus-config.yaml` - Prometheus scraping config (if manual)

**Everything is ready to deploy!** 🚀