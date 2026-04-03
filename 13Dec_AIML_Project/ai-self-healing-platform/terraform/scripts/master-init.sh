#!/bin/bash
# k3s Master Node Initialization Script
# Deployed via Terraform user_data

set -e

echo "========================================="
echo "k3s Master Node Setup"
echo "Cluster: ${cluster_name}"
echo "========================================="

# Update system
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    curl \
    wget \
    git \
    jq \
    apt-transport-https \
    ca-certificates \
    software-properties-common

# Install Docker (for building images)
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu

# Install k3s server
echo "Installing k3s server..."
curl -sfL https://get.k3s.io | sh -s - server \
  --write-kubeconfig-mode 644 \
  --disable traefik \
  --node-name master \
  --cluster-init

# Wait for k3s to be ready
echo "Waiting for k3s to be ready..."
sleep 30

# Verify k3s is running
systemctl status k3s --no-pager

# Install Helm
echo "Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Wait for k3s to be fully operational
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Install Prometheus using Helm
echo "Installing Prometheus..."
kubectl create namespace monitoring || true

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --set server.service.type=NodePort \
  --set server.service.nodePort=30090 \
  --set server.persistentVolume.enabled=false \
  --set alertmanager.enabled=false \
  --set pushgateway.enabled=false

# Wait for Prometheus to be ready
kubectl wait --for=condition=Ready pods -l app=prometheus -n monitoring --timeout=300s

# Create namespace for AI platform
kubectl create namespace ai-platform || true

# Install metrics-server for HPA
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics-server to work with k3s
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-insecure-tls"
  }
]'

# Save cluster token for workers
K3S_TOKEN=$(cat /var/lib/rancher/k3s/server/node-token)
echo "$K3S_TOKEN" > /tmp/k3s-token.txt
chmod 644 /tmp/k3s-token.txt

# Create kubeconfig for external access
MASTER_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
cp /etc/rancher/k3s/k3s.yaml /tmp/k3s-config.yaml
sed -i "s/127.0.0.1/$MASTER_IP/g" /tmp/k3s-config.yaml
chmod 644 /tmp/k3s-config.yaml

# Setup kubectl for ubuntu user
mkdir -p /home/ubuntu/.kube
cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
chown -R ubuntu:ubuntu /home/ubuntu/.kube

# Install useful tools
echo "Installing additional tools..."
snap install helm --classic

# Setup bash completion
kubectl completion bash > /etc/bash_completion.d/kubectl

# Create deployment directory
mkdir -p /home/ubuntu/ai-platform
chown ubuntu:ubuntu /home/ubuntu/ai-platform

# Log completion
echo "========================================="
echo "Master node setup complete!"
echo "Cluster: ${cluster_name}"
echo "Master IP: $MASTER_IP"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Wait for worker nodes to join"
echo "  2. kubectl get nodes"
echo "  3. Deploy AI platform"
echo ""

# Save setup info
cat > /home/ubuntu/cluster-info.txt <<EOF
Cluster Name: ${cluster_name}
Master Node: $(hostname)
Master IP: $MASTER_IP
k3s Version: $(k3s --version | head -n 1)
Setup Date: $(date)

Commands:
  - Check nodes: kubectl get nodes
  - Check pods: kubectl get pods -A
  - Prometheus: http://$MASTER_IP:30090
  
Kubeconfig: /tmp/k3s-config.yaml
Token: /tmp/k3s-token.txt
EOF

chown ubuntu:ubuntu /home/ubuntu/cluster-info.txt

echo "Setup information saved to /home/ubuntu/cluster-info.txt"
