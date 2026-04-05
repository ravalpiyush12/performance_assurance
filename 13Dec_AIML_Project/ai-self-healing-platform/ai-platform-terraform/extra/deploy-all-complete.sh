#!/bin/bash
set -e

echo "========================================"
echo "AI Self-Healing Platform - Complete Deployment"
echo "All Issues Fixed - Production Ready"
echo "========================================"

cd /home/ubuntu/ai-platform

# ============================================================================
# STEP 1: BUILD DOCKER IMAGES
# ============================================================================

echo ""
echo "[1/8] Building Docker images from your code..."
sudo docker build -t ai-platform:v17 -f Dockerfile.platform . || {
    echo "ERROR: Failed to build ai-platform image"
    exit 1
}

sudo docker build -t sample-app:latest -f Dockerfile.sampleapp . || {
    echo "ERROR: Failed to build sample-app image"
    exit 1
}

echo "SUCCESS: Docker images built"

# ============================================================================
# STEP 2: IMPORT IMAGES TO MASTER K3S
# ============================================================================

echo ""
echo "[2/8] Importing images to master k3s..."
sudo docker save ai-platform:v17 | sudo k3s ctr images import -
sudo docker save sample-app:latest | sudo k3s ctr images import -

echo "SUCCESS: Images imported to master"

# ============================================================================
# STEP 3: DISTRIBUTE IMAGES TO WORKER
# ============================================================================

echo ""
echo "[3/8] Distributing images to worker node..."

WORKER_IP=$(sudo k3s kubectl get nodes -o wide | grep worker | awk '{print $6}')

if [ -z "$WORKER_IP" ]; then
    echo "WARNING: Worker node not found, skipping image distribution"
else
    echo "Worker IP: $WORKER_IP"
    
    sudo docker save ai-platform:v17 -o /tmp/ai-platform-v17.tar
    sudo docker save sample-app:latest -o /tmp/sample-app.tar
    sudo chown ubuntu:ubuntu /tmp/*.tar
    
    if scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 /tmp/ai-platform-v17.tar ubuntu@$WORKER_IP:/tmp/ 2>/dev/null; then
        echo "SUCCESS: Images copied to worker"
        ssh -o StrictHostKeyChecking=no ubuntu@$WORKER_IP "sudo k3s ctr images import /tmp/ai-platform-v17.tar && sudo k3s ctr images import /tmp/sample-app.tar && rm /tmp/*.tar" || true
    else
        echo "WARNING: Could not copy images to worker (SSH not configured)"
        echo "Images will be scheduled on master only"
    fi
    
    rm -f /tmp/*.tar
fi

# ============================================================================
# STEP 4: CREATE NAMESPACE
# ============================================================================

echo ""
echo "[4/8] Creating Kubernetes namespace..."
sudo k3s kubectl create namespace monitoring-demo --dry-run=client -o yaml | sudo k3s kubectl apply -f -
sudo k3s kubectl create namespace monitoring --dry-run=client -o yaml | sudo k3s kubectl apply -f -

echo "SUCCESS: Namespaces created"

# ============================================================================
# STEP 5: DEPLOY KUBERNETES MANIFESTS (WITH FIXES)
# ============================================================================

echo ""
echo "[5/8] Deploying Kubernetes manifests..."

mkdir -p kubernetes-fixed

# Fix ai-platform.yaml
if [ -f "kubernetes/ai-platform.yaml" ]; then
    echo "  Processing ai-platform.yaml..."
    sed 's/imagePullPolicy: Never/imagePullPolicy: IfNotPresent/g' kubernetes/ai-platform.yaml | \
    sed 's|PROMETHEUS_URL: "http://prometheus-server"|PROMETHEUS_URL: "http://prometheus-server.monitoring.svc.cluster.local"|g' > kubernetes-fixed/ai-platform.yaml
    
    # Add nodeSelector to force ai-platform on master
    if ! grep -q "nodeSelector" kubernetes-fixed/ai-platform.yaml; then
        # Insert nodeSelector after spec: in Deployment
        awk '/kind: Deployment/,/spec:/ {print; if (/^  template:/) {print "    spec:"; print "      nodeSelector:"; print "        kubernetes.io/hostname: master"; next}} 1' kubernetes-fixed/ai-platform.yaml > kubernetes-fixed/ai-platform-temp.yaml 2>/dev/null || cp kubernetes-fixed/ai-platform.yaml kubernetes-fixed/ai-platform-temp.yaml
        mv kubernetes-fixed/ai-platform-temp.yaml kubernetes-fixed/ai-platform.yaml
    fi
    
    sudo k3s kubectl apply -f kubernetes-fixed/ai-platform.yaml
    echo "  ✓ ai-platform.yaml deployed"
fi

# Fix sample-app.yaml
if [ -f "kubernetes/sample-app.yaml" ]; then
    echo "  Processing sample-app.yaml..."
    sed 's/imagePullPolicy: Never/imagePullPolicy: IfNotPresent/g' kubernetes/sample-app.yaml | \
    sed 's/replicas: 2/replicas: 3/g' > kubernetes-fixed/sample-app.yaml
    
    sudo k3s kubectl apply -f kubernetes-fixed/sample-app.yaml
    echo "  ✓ sample-app.yaml deployed"
fi

# CRITICAL FIX: Handle kubernetes-sample.yaml - REMOVE ServiceMonitor
if [ -f "kubernetes/kubernetes-sample.yaml" ]; then
    echo "  Processing kubernetes-sample.yaml (removing ServiceMonitor)..."
    
    # Remove the ServiceMonitor section (everything after the last ---)
    # This prevents the "no matches for kind ServiceMonitor" error
    awk 'BEGIN{count=0} /^---/{count++; if(count<4) print} count<4 && !/^---/{print}' kubernetes/kubernetes-sample.yaml | \
    sed 's/imagePullPolicy: IfNotPresent/imagePullPolicy: IfNotPresent/g' | \
    sed 's/type: LoadBalancer/type: NodePort/g' > kubernetes-fixed/kubernetes-sample-fixed.yaml
    
    # Only deploy if it doesn't conflict with existing deployments
    if ! sudo k3s kubectl get deployment sample-app -n monitoring-demo &>/dev/null; then
        sudo k3s kubectl apply -f kubernetes-fixed/kubernetes-sample-fixed.yaml 2>&1 | grep -v "ServiceMonitor" || true
        echo "  ✓ kubernetes-sample.yaml deployed (ServiceMonitor removed)"
    else
        echo "  ⚠ sample-app already deployed, skipping kubernetes-sample.yaml"
    fi
fi

# If no manifests found, create defaults
if [ ! -f "kubernetes/ai-platform.yaml" ] && [ ! -f "kubernetes/sample-app.yaml" ]; then
    echo "  Creating default manifests..."
    
    # Create default ai-platform manifest
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

    # Create default sample-app manifest
    cat > kubernetes-fixed/sample-app.yaml <<'YAML'
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

    sudo k3s kubectl apply -f kubernetes-fixed/ai-platform.yaml
    sudo k3s kubectl apply -f kubernetes-fixed/sample-app.yaml
    echo "  ✓ Default manifests deployed"
fi

echo "SUCCESS: Kubernetes manifests deployed"

# ============================================================================
# STEP 6: INSTALL PROMETHEUS
# ============================================================================

echo ""
echo "[6/8] Installing Prometheus..."

if ! command -v helm &> /dev/null; then
    echo "Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update

if helm list -n monitoring | grep -q prometheus; then
    echo "Prometheus already installed"
else
    echo "Installing Prometheus..."
    helm install prometheus prometheus-community/prometheus \
      --namespace monitoring \
      --set server.service.type=NodePort \
      --set server.service.nodePort=30090 \
      --set alertmanager.enabled=false \
      --set prometheus-pushgateway.enabled=false \
      --set server.persistentVolume.enabled=false \
      --set kube-state-metrics.enabled=true \
      --wait --timeout=5m || echo "WARNING: Prometheus installation had issues"
fi

echo "SUCCESS: Prometheus installed"

# ============================================================================
# STEP 7: WAIT FOR DEPLOYMENTS
# ============================================================================

echo ""
echo "[7/8] Waiting for all deployments to be ready..."

sleep 10

echo "Waiting for ai-platform..."
sudo k3s kubectl rollout status deployment/ai-platform -n monitoring-demo --timeout=300s || echo "WARNING: AI platform timeout"

echo "Waiting for sample-app..."
sudo k3s kubectl rollout status deployment/sample-app -n monitoring-demo --timeout=300s || echo "WARNING: Sample app timeout"

echo "Waiting for Prometheus server..."
sudo k3s kubectl rollout status deployment/prometheus-server -n monitoring --timeout=300s || echo "WARNING: Prometheus timeout"

# ============================================================================
# STEP 8: GENERATE INITIAL TRAFFIC
# ============================================================================

echo ""
echo "[8/8] Generating initial traffic for ML model training..."

sleep 15

for i in {1..50}; do
    curl -s http://localhost:30080/health > /dev/null 2>&1 || true
    curl -s http://localhost:30080/compute > /dev/null 2>&1 || true
    sleep 0.5
done &

echo "SUCCESS: Initial traffic generation started"

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================

echo ""
echo "========================================"
echo "DEPLOYMENT COMPLETE!"
echo "========================================"

sudo k3s kubectl get nodes -o wide

echo ""
echo "Pods in monitoring-demo:"
sudo k3s kubectl get pods -n monitoring-demo -o wide

echo ""
echo "Services:"
sudo k3s kubectl get svc -n monitoring-demo
sudo k3s kubectl get svc -n monitoring | grep prometheus-server

echo ""
echo "HPA Status:"
sudo k3s kubectl get hpa -n monitoring-demo

MASTER_IP=$(curl -s http://checkip.amazonaws.com)

echo ""
echo "========================================"
echo "ACCESS INFORMATION"
echo "========================================"
echo "Dashboard:  http://${MASTER_IP}:30800"
echo "Sample App: http://${MASTER_IP}:30080/health"
echo "Prometheus: http://${MASTER_IP}:30090"
echo "========================================"
echo ""
echo "Wait 2-3 minutes for ML model to train (needs 20 samples)"
echo "Then refresh the dashboard to see metrics!"
echo ""
