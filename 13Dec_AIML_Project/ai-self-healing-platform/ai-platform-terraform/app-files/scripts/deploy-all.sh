#!/bin/bash
set -e

echo "========================================"
echo "AI Self-Healing Platform - Single Node"
echo "Final Production Deployment"
echo "========================================"

cd /home/ubuntu/ai-platform

# ============================================================================
# STEP 1: BUILD DOCKER IMAGES
# ============================================================================

echo ""
echo "[1/7] Building Docker images..."
sudo docker build -t ai-platform:v17 -f Dockerfile.platform . || exit 1
sudo docker build -t sample-app:latest -f Dockerfile.sampleapp . || exit 1
echo "SUCCESS: Images built"

# ============================================================================
# STEP 2: IMPORT TO K3S
# ============================================================================

echo ""
echo "[2/7] Importing images to k3s..."
sudo docker save ai-platform:v17 | sudo k3s ctr images import -
sudo docker save sample-app:latest | sudo k3s ctr images import -
echo "SUCCESS: Images imported"

# ============================================================================
# STEP 3: CREATE NAMESPACES
# ============================================================================

echo ""
echo "[3/7] Creating namespaces..."
sudo k3s kubectl create namespace monitoring-demo --dry-run=client -o yaml | sudo k3s kubectl apply -f -
sudo k3s kubectl create namespace monitoring --dry-run=client -o yaml | sudo k3s kubectl apply -f -
echo "SUCCESS: Namespaces created"

# ============================================================================
# STEP 4: INSTALL PROMETHEUS (WITH RETRY)
# ============================================================================

echo ""
echo "[4/7] Installing Prometheus..."

# Set KUBECONFIG for Helm
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Install Helm if not present
if ! command -v helm &> /dev/null; then
    echo "Installing Helm..."
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

# Add Prometheus repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update

# Delete if exists
helm uninstall prometheus -n monitoring 2>/dev/null || true
sleep 5

# Clean up old resources
sudo k3s kubectl delete deployment prometheus-server -n monitoring --ignore-not-found
sudo k3s kubectl delete svc prometheus-server -n monitoring --ignore-not-found
sudo k3s kubectl delete configmap prometheus-server -n monitoring --ignore-not-found
sleep 5

# Install Prometheus
echo "Installing Prometheus with pod discovery..."
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --set server.service.type=NodePort \
  --set server.service.nodePort=30090 \
  --set alertmanager.enabled=false \
  --set prometheus-pushgateway.enabled=false \
  --set server.persistentVolume.enabled=false \
  --set kube-state-metrics.enabled=true \
  --wait --timeout=5m

# Wait for Prometheus
echo "Waiting for Prometheus..."
sudo k3s kubectl rollout status deployment/prometheus-server -n monitoring --timeout=300s
echo "SUCCESS: Prometheus installed"

# ============================================================================
# STEP 5: DEPLOY APPLICATIONS
# ============================================================================

echo ""
echo "[5/7] Deploying applications..."

# Deploy or use defaults
if [ -f "kubernetes/ai-platform.yaml" ]; then
    sudo k3s kubectl apply -f kubernetes/ai-platform.yaml
elif [ -f "kubernetes-fixed/ai-platform.yaml" ]; then
    sudo k3s kubectl apply -f kubernetes-fixed/ai-platform.yaml
else
    # Create default
    cat > /tmp/ai-platform.yaml <<'YAML'
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
      containers:
      - name: platform
        image: ai-platform:v17
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: ai-platform-config
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
    sudo k3s kubectl apply -f /tmp/ai-platform.yaml
fi

# Deploy sample-app
if [ -f "kubernetes/sample-app.yaml" ]; then
    sudo k3s kubectl apply -f kubernetes/sample-app.yaml
else
    cat > /tmp/sample-app.yaml <<'YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
  namespace: monitoring-demo
spec:
  replicas: 3
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
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
YAML
    sudo k3s kubectl apply -f /tmp/sample-app.yaml
fi

echo "SUCCESS: Applications deployed"

# ============================================================================
# STEP 6: WAIT FOR DEPLOYMENTS
# ============================================================================

echo ""
echo "[6/7] Waiting for deployments..."
sleep 10

sudo k3s kubectl rollout status deployment/ai-platform -n monitoring-demo --timeout=300s || echo "WARNING: AI platform timeout"
sudo k3s kubectl rollout status deployment/sample-app -n monitoring-demo --timeout=300s || echo "WARNING: Sample app timeout"

echo "SUCCESS: Deployments ready"

# ============================================================================
# STEP 7: GENERATE INITIAL TRAFFIC
# ============================================================================

echo ""
echo "[7/7] Generating initial traffic..."
sleep 15

for i in {1..50}; do
    curl -s http://localhost:30080/health > /dev/null 2>&1 || true
    curl -s http://localhost:30080/compute > /dev/null 2>&1 || true
    sleep 0.5
done &

echo "SUCCESS: Traffic generation started"

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================

echo ""
echo "========================================"
echo "DEPLOYMENT COMPLETE!"
echo "========================================"

sudo k3s kubectl get nodes
echo ""
sudo k3s kubectl get pods -n monitoring-demo
echo ""
sudo k3s kubectl get svc -n monitoring-demo
echo ""
sudo k3s kubectl get svc -n monitoring | grep prometheus

MASTER_IP=$(curl -s http://checkip.amazonaws.com)

echo ""
echo "========================================"
echo "ACCESS URLS"
echo "========================================"
echo "Dashboard:  http://${MASTER_IP}:30800"
echo "Sample App: http://${MASTER_IP}:30080/health"
echo "Prometheus: http://${MASTER_IP}:30090"
echo "========================================"
echo ""
echo "Platform is ready for MTech demonstration!"
echo ""
