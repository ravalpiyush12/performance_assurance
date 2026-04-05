#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  AI Self-Healing Platform - Deploying YOUR Actual Code    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /home/ubuntu/ai-platform

# ============================================================================
# STEP 1: BUILD DOCKER IMAGES FROM YOUR CODE
# ============================================================================

echo "📦 Building Docker images from your code..."

# Check if Dockerfiles exist
if [ ! -f "Dockerfile.platform" ]; then
    echo "❌ ERROR: Dockerfile.platform not found!"
    echo "Please ensure your files were uploaded correctly."
    exit 1
fi

# Build AI Platform
echo "  Building ai-platform:v17..."
sudo docker build -t ai-platform:v17 -f Dockerfile.platform . || {
    echo "❌ Failed to build AI platform image"
    exit 1
}

# Build Sample App
if [ -f "Dockerfile.sampleapp" ]; then
    echo "  Building sample-app:latest..."
    sudo docker build -t sample-app:latest -f Dockerfile.sampleapp .
else
    echo "  ⚠ Dockerfile.sampleapp not found, creating default..."
    cat > Dockerfile.sampleapp <<'DOCKERFILE'
FROM python:3.9-slim
WORKDIR /app
RUN pip install --no-cache-dir flask prometheus-client
COPY sample-app.py .
EXPOSE 5000
CMD ["python", "sample-app.py"]
DOCKERFILE

    # Create basic sample-app.py if not exists
    if [ ! -f "sample-app.py" ]; then
        cat > sample-app.py <<'PYTHON'
from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time, random

app = Flask(__name__)
requests_total = Counter('http_requests_total', 'Total requests')
request_duration = Histogram('http_request_duration_seconds', 'Request duration')
errors_total = Counter('http_errors_total', 'Total errors')

@app.route('/health')
@request_duration.time()
def health():
    requests_total.inc()
    return jsonify({"status": "healthy", "service": "sample-app"})

@app.route('/compute')
@request_duration.time()
def compute():
    requests_total.inc()
    result = sum(i**2 for i in range(50000))
    time.sleep(random.uniform(0.1, 0.3))
    return jsonify({"result": result, "status": "computed"})

@app.route('/error')
def error_endpoint():
    errors_total.inc()
    return jsonify({"error": "Simulated error"}), 500

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
PYTHON
    fi
    
    sudo docker build -t sample-app:latest -f Dockerfile.sampleapp .
fi

echo "✅ Docker images built successfully"

# ============================================================================
# STEP 2: IMPORT IMAGES TO K3S
# ============================================================================

echo ""
echo "📥 Importing images to k3s containerd..."
sudo docker save ai-platform:v17 | sudo k3s ctr images import -
sudo docker save sample-app:latest | sudo k3s ctr images import -

# Verify images imported
echo ""
echo "Verifying images in k3s:"
sudo k3s ctr -n k8s.io images ls | grep -E "ai-platform|sample-app"

echo "✅ Images imported to k3s"

# ============================================================================
# STEP 3: FIX KUBERNETES MANIFESTS
# ============================================================================

echo ""
echo "🔧 Preparing Kubernetes manifests..."

mkdir -p kubernetes-fixed

# Fix ai-platform.yaml
if [ -f "ai-platform.yaml" ]; then
    echo "  Fixing ai-platform.yaml..."
    # Fix image pull policy and Prometheus URL
    sed 's/imagePullPolicy: Never/imagePullPolicy: IfNotPresent/g' ai-platform.yaml | \
    sed 's|PROMETHEUS_URL: "http://prometheus-server"|PROMETHEUS_URL: "http://prometheus-server.monitoring.svc.cluster.local"|g' > kubernetes-fixed/ai-platform.yaml
else
    echo "  ⚠ ai-platform.yaml not found, using default"
    cat > kubernetes-fixed/ai-platform.yaml <<'YAML'
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-platform-config
  namespace: monitoring-demo
data:
  MODE: "production"
  PROMETHEUS_URL: "http://prometheus-server.monitoring.svc.cluster.local"
  PROMETHEUS_ENABLED: "true"
  KUBERNETES_ENABLED: "true"
  AUTO_METRICS_ENABLED: "true"
  TARGET_APP: "sample-app"
  TARGET_NAMESPACE: "monitoring-demo"
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ai-platform
  namespace: monitoring-demo
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ai-platform-role
rules:
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["autoscaling"]
  resources: ["horizontalpodautoscalers"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ai-platform-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: ai-platform-role
subjects:
- kind: ServiceAccount
  name: ai-platform
  namespace: monitoring-demo
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-platform
  namespace: monitoring-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ai-platform
  template:
    metadata:
      labels:
        app: ai-platform
    spec:
      serviceAccountName: ai-platform
      nodeSelector:
        kubernetes.io/hostname: master
      containers:
      - name: platform
        image: ai-platform:v17
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: ai-platform-config
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: ai-platform
  namespace: monitoring-demo
spec:
  type: NodePort
  selector:
    app: ai-platform
  ports:
  - port: 80
    targetPort: 8000
    nodePort: 30800
YAML
fi

# Fix sample-app.yaml
if [ -f "sample-app.yaml" ]; then
    echo "  Fixing sample-app.yaml..."
    # Fix image pull policy and ensure proper resources
    sed 's/imagePullPolicy: Never/imagePullPolicy: IfNotPresent/g' sample-app.yaml | \
    sed 's/replicas: 2/replicas: 4/g' > kubernetes-fixed/sample-app.yaml
else
    echo "  ⚠ sample-app.yaml not found, using default"
    cat > kubernetes-fixed/sample-app.yaml <<'YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
  namespace: monitoring-demo
spec:
  replicas: 4
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "5000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: sample-app
        image: sample-app:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 5000
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: sample-app
  namespace: monitoring-demo
spec:
  type: NodePort
  selector:
    app: sample-app
  ports:
  - port: 80
    targetPort: 5000
    nodePort: 30080
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sample-app-hpa
  namespace: monitoring-demo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sample-app
  minReplicas: 4
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
YAML
fi

echo "✅ Kubernetes manifests prepared"

# ============================================================================
# STEP 4: DEPLOY TO KUBERNETES
# ============================================================================

echo ""
echo "🚀 Deploying to Kubernetes cluster..."

# Deploy in correct order
echo "  1. Deploying ai-platform (ConfigMap, RBAC, Deployment, Service)..."
sudo k3s kubectl apply -f kubernetes-fixed/ai-platform.yaml

echo "  2. Deploying sample-app (Deployment, Service, HPA)..."
sudo k3s kubectl apply -f kubernetes-fixed/sample-app.yaml

# ============================================================================
# STEP 5: WAIT FOR DEPLOYMENTS
# ============================================================================

echo ""
echo "⏳ Waiting for deployments to be ready..."

echo "  Waiting for ai-platform..."
sudo k3s kubectl rollout status deployment/ai-platform -n monitoring-demo --timeout=300s || {
    echo "❌ AI Platform deployment timeout"
    sudo k3s kubectl logs -l app=ai-platform -n monitoring-demo --tail=50
}

echo "  Waiting for sample-app..."
sudo k3s kubectl rollout status deployment/sample-app -n monitoring-demo --timeout=300s || {
    echo "❌ Sample App deployment timeout"
    sudo k3s kubectl logs -l app=sample-app -n monitoring-demo --tail=20
}

# Wait for HPA to initialize
echo "  Waiting for HPA to initialize (90 seconds)..."
sleep 90

# ============================================================================
# STEP 6: VERIFY DEPLOYMENT
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  DEPLOYMENT COMPLETE!                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

MASTER_IP=$(curl -s http://checkip.amazonaws.com)

echo "📊 Cluster Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo k3s kubectl get nodes -o wide

echo ""
echo "📦 Pod Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo k3s kubectl get pods -n monitoring-demo -o wide

echo ""
echo "🌐 Services:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo k3s kubectl get svc -n monitoring-demo

echo ""
echo "📈 HPA Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo k3s kubectl get hpa -n monitoring-demo

echo ""
echo "🔗 Access URLs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Dashboard:  http://${MASTER_IP}:30800"
echo "  Sample App: http://${MASTER_IP}:30080/health"
echo "  Prometheus: http://${MASTER_IP}:30090"
echo ""

# Check if dashboard is responding
echo "🔍 Testing endpoints..."
if curl -s -f http://localhost:30800/api/v1/status > /dev/null 2>&1; then
    echo "  ✅ AI Platform API responding"
else
    echo "  ⚠️  AI Platform API not ready (may need 1-2 more minutes)"
fi

if curl -s -f http://localhost:30080/health > /dev/null 2>&1; then
    echo "  ✅ Sample App responding"
else
    echo "  ⚠️  Sample App not ready"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🎉 SUCCESS! Your AI Platform is Ready!                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Open dashboard: http://${MASTER_IP}:30800"
echo "  2. Run load test: ./load-test.ps1 -MasterIP \"${MASTER_IP}\""
echo "  3. Watch self-healing in action!"
echo ""
