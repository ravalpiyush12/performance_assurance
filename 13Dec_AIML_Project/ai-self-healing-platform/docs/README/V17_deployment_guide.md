# 🚀 V17 DEPLOYMENT & TESTING GUIDE

Complete guide for deploying the production-ready v17 with Prometheus & Kubernetes integration.

---

## 🎯 **WHAT'S NEW IN V17**

### **Major Changes:**

| Feature | v16 | v17 |
|---------|-----|-----|
| **Metrics Source** | test_load.py (simulated) | Prometheus (REAL metrics) |
| **Target Application** | None | sample-app (Flask app) |
| **Kubernetes Integration** | No | Yes (scales deployments) |
| **Production Ready** | Simulated | REAL system monitoring |
| **HPA Trigger** | Manual | Automatic via K8s API |

---

## 📋 **INSTALLATION**

### **STEP 1: Install Dependencies**

```powershell
cd "F:\Piyush Data\Learning\performance_assurance\13Dec_AIML_Project\ai-self-healing-platform"

# Install new requirements
& "F:/Piyush Data/Learning/performance_assurance/13Dec_AIML_Project/.venv/Scripts/python.exe" -m pip install prometheus-api-client kubernetes Flask prometheus-flask-exporter
```

**Or install from requirements:**
```powershell
& "F:/Piyush Data/Learning/performance_assurance/13Dec_AIML_Project/.venv/Scripts/python.exe" -m pip install -r requirements_v17.txt
```

---

### **STEP 2: Replace main.py**

```powershell
# Backup v16
Copy-Item "src\api\main.py" -Destination "src\api\main_v16_backup.py"

# Copy v17
Copy-Item "$env:USERPROFILE\Downloads\main_v17_prometheus_k8s.py" -Destination "src\api\main.py"
```

---

## 🧪 **TESTING SCENARIOS**

### **SCENARIO 1: Local Development Mode (No Prometheus/K8s)**

**Use case:** Testing on your PC without Kubernetes

**Command:**
```powershell
# Start in development mode (auto-generates metrics)
& "F:/Piyush Data/Learning/performance_assurance/13Dec_AIML_Project/.venv/Scripts/python.exe" -m uvicorn src.api.main:app --reload --port 8000
```

**Expected:**
```
MODE: DEVELOPMENT
Prometheus: ❌ Disabled
Kubernetes: ❌ Disabled
Auto-Metrics: ✅ ENABLED
✅ Auto-metrics generator started
```

**Verify:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health | ConvertFrom-Json
# mode: "development"
# auto_metrics: true
# prometheus_enabled: false
# kubernetes_enabled: false
```

---

### **SCENARIO 2: Production Mode with Manual Metrics (test_load.py)**

**Use case:** Testing production mode locally without Prometheus

**Terminal 1 (Platform):**
```powershell
$env:MODE="production"
& "F:/Piyush Data/Learning/performance_assurance/13Dec_AIML_Project/.venv/Scripts/python.exe" -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 (Load Tester):**
```powershell
& "F:/Piyush Data/Learning/performance_assurance/13Dec_AIML_Project/.venv/Scripts/python.exe" test_load.py --duration 60 --rate 10 --anomaly-chance 0.15
```

**Expected:**
- Platform receives metrics via API
- Detects anomalies
- Executes self-healing actions
- No Kubernetes scaling (K8s not enabled)

---

### **SCENARIO 3: Production with Prometheus (Minikube)**

**Use case:** Full production setup with Prometheus on local Kubernetes

#### **Prerequisites:**

1. **Install Minikube** (free local Kubernetes)
```powershell
choco install minikube
minikube start --memory=4096 --cpus=2
```

2. **Install Helm** (Kubernetes package manager)
```powershell
choco install kubernetes-helm
```

#### **Deploy Components:**

**Step 1: Deploy Prometheus**
```bash
# Add Prometheus repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/prometheus \
  --set server.service.type=NodePort \
  --set server.service.nodePort=30090

# Get Prometheus URL
minikube service prometheus-server --url
# Example output: http://192.168.49.2:30090
```

**Step 2: Deploy Sample App**
```bash
# Build Docker image
docker build -t sample-app:v1 -f Dockerfile.sampleapp .

# Load into Minikube
minikube image load sample-app:v1

# Deploy
kubectl apply -f kubernetes/sample-app-deployment.yaml

# Get external IP
minikube service sample-app --url
# Example output: http://192.168.49.2:30080
```

**Step 3: Deploy AI Platform (v17)**
```bash
# Build Docker image
docker build -t ai-platform:v17 .

# Load into Minikube
minikube image load ai-platform:v17

# Create ConfigMap with Prometheus URL
kubectl create configmap ai-platform-config \
  --from-literal=MODE=production \
  --from-literal=PROMETHEUS_URL=http://prometheus-server:80 \
  --from-literal=PROMETHEUS_ENABLED=true \
  --from-literal=KUBERNETES_ENABLED=true \
  --from-literal=TARGET_APP=sample-app \
  --from-literal=TARGET_NAMESPACE=default

# Deploy
kubectl apply -f kubernetes/ai-platform-deployment.yaml

# Get platform URL
minikube service ai-platform --url
```

**Step 4: Test End-to-End**
```bash
# Terminal 1: Watch pods
kubectl get pods -w

# Terminal 2: Run JMeter against sample-app
# (Get sample-app URL from: minikube service sample-app --url)
jmeter -n -t jmeter-test-plan.jmx \
  -Jhost=192.168.49.2 \
  -Jport=30080 \
  -l results.jtl

# Terminal 3: Watch AI platform logs
kubectl logs -f deployment/ai-platform

# Terminal 4: Watch HPA
kubectl get hpa -w
```

**What You'll See:**

**Terminal 1 (Pods):**
```
sample-app-abc123   Running   85% CPU
sample-app-def456   Running   82% CPU
sample-app-ghi789   Pending   0%      ← New pod being created
sample-app-ghi789   Running   45% CPU  ← Now running, load distributed
```

**Terminal 3 (AI Platform Logs):**
```
📊 Prometheus → CPU=85.3% Memory=72.1% Latency=1850ms
⚠️  Anomaly detected: CPU_USAGE (severity: critical, score: -0.621)
✅ Action decided: scale_up for CPU_USAGE
🎯 Triggering K8s scaling: sample-app 2 → 4
✅ Scaled sample-app from 2 → 4 replicas
📊 Prometheus → CPU=42.5% Memory=68.3% Latency=380ms  ← Recovered!
```

**Terminal 4 (HPA):**
```
NAME              REFERENCE          TARGETS   MINPODS   MAXPODS   REPLICAS
sample-app-hpa    Deployment/...     85%/70%   2         10        2
sample-app-hpa    Deployment/...     85%/70%   2         10        4  ← Scaled!
sample-app-hpa    Deployment/...     42%/70%   2         10        4  ← Stabilized
```

---

## 🔧 **CONFIGURATION OPTIONS**

### **Environment Variables:**

```bash
# Core Settings
MODE=production                          # or "development"
PORT=8000

# Prometheus
PROMETHEUS_URL=http://prometheus-server:9090
PROMETHEUS_ENABLED=true                  # Enable Prometheus integration

# Kubernetes
KUBERNETES_ENABLED=true                  # Enable K8s API calls
TARGET_APP=sample-app                    # Application to monitor
TARGET_NAMESPACE=default                 # K8s namespace

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Development Mode
AUTO_GENERATE_INTERVAL=2                 # Seconds between metrics
AUTO_ANOMALY_MIN=25                      # Min metrics before anomaly
AUTO_ANOMALY_MAX=35                      # Max metrics before anomaly
```

---

## 📊 **API ENDPOINTS (NEW in v17)**

### **Target App Management:**

```bash
# Get target app info
GET /api/v1/target-app/info

# Example response:
{
  "name": "sample-app",
  "namespace": "default",
  "replicas": 4,
  "ready_replicas": 4,
  "available_replicas": 4
}

# Manually scale target app (admin only)
POST /api/v1/target-app/scale?replicas=6
Authorization: Bearer <admin-token>

# Response:
{
  "status": "success",
  "message": "Scaled sample-app to 6 replicas"
}
```

### **System Status (Enhanced):**

```bash
GET /api/v1/status

# New fields in v17:
{
  "health_score": 92.5,
  "mode": "production",
  "prometheus_enabled": true,
  "kubernetes_enabled": true,
  "target_app": "sample-app",
  ...
}
```

---

## 🎬 **DEMO SCRIPT FOR PRESENTATION**

### **Setup (Before Presentation):**

```bash
# 1. Start Minikube
minikube start

# 2. Deploy all components
helm install prometheus prometheus-community/prometheus
kubectl apply -f kubernetes/sample-app-deployment.yaml
kubectl apply -f kubernetes/ai-platform-deployment.yaml

# 3. Verify all running
kubectl get pods
# All pods should be "Running"

# 4. Open terminals:
# - Terminal 1: kubectl get pods -w
# - Terminal 2: kubectl logs -f deployment/ai-platform
# - Terminal 3: kubectl get hpa -w
# - Terminal 4: JMeter (ready to run)
```

### **During Demo (3-5 minutes):**

**Slide 1: Architecture**
> "Let me show you the complete production architecture running on Kubernetes..."

[Show architecture diagram]

**Slide 2: Normal Operation**
> "Here's the system in normal operation. The sample application is running with 2 pods, CPU around 45%."

[Show Terminal 1: `kubectl get pods`]

**Slide 3: Start Load Test**
> "Now I'll simulate production load using JMeter, sending 1000 requests per second to the compute-intensive endpoint..."

[Terminal 4: Start JMeter]
```bash
jmeter -n -t test-plan.jmx -l results.jtl
```

**Slide 4: Watch Metrics**
> "Watch the AI platform receiving REAL metrics from Prometheus..."

[Terminal 2: Platform logs showing Prometheus metrics]

**Slide 5: Anomaly Detection**
> "There! CPU reached 85% - the platform detected this anomaly..."

[Terminal 2: Show anomaly detection log]

**Slide 6: Auto-Scaling**
> "And it's automatically triggering Kubernetes to scale the application..."

[Terminal 1: Show pods scaling 2 → 4]
[Terminal 3: Show HPA scaling]

**Slide 7: Recovery**
> "As the new pods come online, CPU drops back to normal levels. The system healed itself automatically."

[Terminal 2: Show recovery in logs]

**Slide 8: Summary**
> "In this test, the platform detected 8 anomalies, executed 5 scaling actions, and maintained 99.8% uptime throughout."

[Show summary stats from /api/v1/status]

---

## ✅ **VERIFICATION CHECKLIST**

### **After Deployment:**

```bash
# 1. Check platform health
curl http://<PLATFORM-URL>/health

# Should return:
# {
#   "status": "healthy",
#   "mode": "production",
#   "prometheus_enabled": true,
#   "kubernetes_enabled": true,
#   "target_app": "sample-app"
# }

# 2. Check target app info
curl http://<PLATFORM-URL>/api/v1/target-app/info

# Should return deployment info

# 3. Check Prometheus connection
kubectl logs deployment/ai-platform | grep Prometheus

# Should see: "✅ Prometheus connected"

# 4. Check K8s connection
kubectl logs deployment/ai-platform | grep Kubernetes

# Should see: "✅ Kubernetes client initialized"

# 5. Trigger test anomaly
# Hit sample-app /compute endpoint 100 times rapidly
for i in {1..100}; do curl http://<SAMPLE-APP-URL>/compute & done

# 6. Watch platform logs
kubectl logs -f deployment/ai-platform

# Should see anomaly detection and scaling action
```

---

## 🆘 **TROUBLESHOOTING**

### **Issue 1: "Prometheus not available"**

```bash
# Check Prometheus is running
kubectl get pods | grep prometheus

# Check Prometheus URL is correct
kubectl get svc prometheus-server
# Use the ClusterIP, e.g., http://prometheus-server:80

# Update ConfigMap
kubectl edit configmap ai-platform-config
# Set PROMETHEUS_URL=http://prometheus-server:80
```

---

### **Issue 2: "Kubernetes client not available"**

```bash
# Check service account permissions
kubectl get serviceaccount
kubectl get clusterrolebinding

# Create service account with permissions
kubectl apply -f kubernetes/ai-platform-rbac.yaml
```

---

### **Issue 3: "Target app not found"**

```bash
# Check sample-app is deployed
kubectl get deployment sample-app

# Check namespace
kubectl get deployment sample-app -n default

# Update ConfigMap
kubectl edit configmap ai-platform-config
# Set TARGET_APP=sample-app
# Set TARGET_NAMESPACE=default
```

---

## 📈 **SUCCESS METRICS**

After full deployment, you should have:

- ✅ **3 deployments running:** sample-app, ai-platform, prometheus
- ✅ **Metrics flowing:** Prometheus → AI Platform every 15s
- ✅ **Anomaly detection working:** Platform detects CPU/Memory spikes
- ✅ **Auto-scaling working:** K8s scales sample-app based on load
- ✅ **HPA functional:** Maintains target CPU utilization
- ✅ **End-to-end flow:** JMeter → Sample App → Prometheus → AI Platform → K8s HPA

---

## 🎯 **NEXT STEPS**

1. ✅ Test v17 locally (development mode)
2. ✅ Install Minikube
3. ✅ Deploy to Minikube with Prometheus
4. ✅ Test end-to-end flow
5. ✅ Prepare demo
6. 🚀 Deploy to AWS EKS (production)

---

**You now have a REAL production-ready self-healing platform!** 🎉