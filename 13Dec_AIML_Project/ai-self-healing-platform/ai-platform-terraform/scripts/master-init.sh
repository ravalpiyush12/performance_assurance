#!/bin/bash
set -e

# Update system
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y \
    curl \
    wget \
    git \
    jq \
    python3 \
    python3-pip \
    docker.io

# Start Docker
systemctl enable docker
systemctl start docker

# Install k3s (master)
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
    --node-name=master \
    --disable traefik \
    --write-kubeconfig-mode=644 \
    --token=${k3s_token}" sh -

# Wait for k3s to be ready
echo "Waiting for k3s to start..."
timeout 120 bash -c 'until k3s kubectl get nodes | grep -q master; do sleep 2; done'

# Install metrics-server
echo "Installing metrics-server..."
k3s kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics-server for kubelet insecure TLS
k3s kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

# Create namespace
k3s kubectl create namespace monitoring-demo || true
k3s kubectl create namespace monitoring || true

# Install Prometheus (minimal)
cat <<'PROM_EOF' | k3s kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
            namespaces:
              names:
                - monitoring-demo
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)
          - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
            action: replace
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: $1:$2
            target_label: __address__
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus-server
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus-server
  template:
    metadata:
      labels:
        app: prometheus-server
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.45.0
        args:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus/'
          - '--storage.tsdb.retention.time=1h'
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-server
  namespace: monitoring
spec:
  type: NodePort
  selector:
    app: prometheus-server
  ports:
  - port: 80
    targetPort: 9090
    nodePort: 30090
PROM_EOF

# Setup project directory
mkdir -p /home/ubuntu/ai-platform/{src,kubernetes,scripts}
cd /home/ubuntu/ai-platform

# Clone or setup application files
# For now, we'll create them in the deploy script

# Set ownership
chown -R ubuntu:ubuntu /home/ubuntu/ai-platform

echo "Master node initialization complete!"
echo "k3s token: ${k3s_token}"
