#!/bin/bash
set -e

echo "========================================"
echo "AI Self-Healing Platform - Full Deployment"
echo "========================================"

cd /home/ubuntu/ai-platform

# Create application source files
echo "Creating application source files..."

# Sample App
cat > sample-app.py <<'EOF'
from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import random

app = Flask(__name__)

# Prometheus metrics
requests_total = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
errors_total = Counter('http_errors_total', 'Total HTTP errors')

@app.route('/health')
@request_duration.time()
def health():
    requests_total.inc()
    return jsonify({"status": "healthy", "service": "sample-app"})

@app.route('/compute')
@request_duration.time()
def compute():
    requests_total.inc()
    # CPU intensive task
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
EOF

# AI Platform (simplified version for deployment)
cat > ai-platform.py <<'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI(title="AI Self-Healing Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/status")
def get_status():
    return {
        "health_score": 100.0,
        "prometheus_enabled": os.getenv("PROMETHEUS_ENABLED", "false") == "true",
        "kubernetes_enabled": os.getenv("KUBERNETES_ENABLED", "false") == "true",
        "mode": os.getenv("MODE", "production"),
        "ml_model_trained": True
    }

@app.get("/")
def root():
    return {"message": "AI Self-Healing Platform API", "version": "v17"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Create Dockerfiles
cat > Dockerfile.sampleapp <<'DOCKERFILE'
FROM python:3.9-slim
WORKDIR /app
RUN pip install flask prometheus-client
COPY sample-app.py .
EXPOSE 5000
CMD ["python", "sample-app.py"]
DOCKERFILE

cat > Dockerfile.platform <<'DOCKERFILE'
FROM python:3.9-slim
WORKDIR /app
RUN pip install fastapi uvicorn[standard]
COPY ai-platform.py .
EXPOSE 8000
CMD ["python", "ai-platform.py"]
DOCKERFILE

# Build Docker images
echo "Building Docker images..."
sudo docker build -t sample-app:latest -f Dockerfile.sampleapp .
sudo docker build -t ai-platform:v17 -f Dockerfile.platform .

# Export and import to k3s
echo "Importing images to k3s..."
sudo docker save sample-app:latest | sudo k3s ctr images import -
sudo docker save ai-platform:v17 | sudo k3s ctr images import -

# Create Kubernetes manifests
echo "Creating Kubernetes manifests..."

# RBAC
cat > kubernetes/rbac.yaml <<'YAML'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ai-platform
  namespace: monitoring-demo
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ai-platform-role
  namespace: monitoring-demo
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale"]
  verbs: ["get", "list", "watch", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ai-platform-rolebinding
  namespace: monitoring-demo
subjects:
- kind: ServiceAccount
  name: ai-platform
  namespace: monitoring-demo
roleRef:
  kind: Role
  name: ai-platform-role
  apiGroup: rbac.authorization.k8s.io
YAML

# ConfigMap
cat > kubernetes/configmap.yaml <<'YAML'
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
  TARGET_APP: "sample-app"
  TARGET_NAMESPACE: "monitoring-demo"
YAML

# Sample App Deployment (distributed across nodes)
cat > kubernetes/sample-app.yaml <<'YAML'
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
    protocol: TCP
YAML

# AI Platform Deployment (master only)
cat > kubernetes/ai-platform.yaml <<'YAML'
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
    protocol: TCP
YAML

# HPA
cat > kubernetes/hpa.yaml <<'YAML'
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sample-app
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

# Deploy everything
echo "Deploying to Kubernetes..."
sudo k3s kubectl apply -f kubernetes/rbac.yaml
sudo k3s kubectl apply -f kubernetes/configmap.yaml
sudo k3s kubectl apply -f kubernetes/sample-app.yaml
sudo k3s kubectl apply -f kubernetes/ai-platform.yaml

# Wait for deployments
echo "Waiting for deployments to be ready..."
sudo k3s kubectl rollout status deployment/sample-app -n monitoring-demo --timeout=300s
sudo k3s kubectl rollout status deployment/ai-platform -n monitoring-demo --timeout=300s

# Create HPA (after deployments are ready)
sleep 10
sudo k3s kubectl apply -f kubernetes/hpa.yaml

# Wait for HPA to start working
echo "Waiting for HPA to initialize..."
sleep 60

# Display status
echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
sudo k3s kubectl get nodes
echo ""
sudo k3s kubectl get pods -n monitoring-demo -o wide
echo ""
sudo k3s kubectl get svc -n monitoring-demo
echo ""
sudo k3s kubectl get hpa -n monitoring-demo
echo ""
echo "Dashboard: http://$(curl -s http://checkip.amazonaws.com):30800"
echo "Sample App: http://$(curl -s http://checkip.amazonaws.com):30080/health"
echo "Prometheus: http://$(curl -s http://checkip.amazonaws.com):30090"
echo "=========================================="
