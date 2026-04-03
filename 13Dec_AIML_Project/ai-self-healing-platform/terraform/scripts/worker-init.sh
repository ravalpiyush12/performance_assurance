#!/bin/bash
# k3s Worker Node Initialization Script
# Deployed via Terraform user_data

set -e

echo "========================================="
echo "k3s Worker Node Setup"
echo "Master: ${master_private_ip}"
echo "========================================="

# Update system
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y curl wget git

# Install Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu

# Wait for master to be fully ready
echo "Waiting for master node to be ready..."
sleep 120

# Get k3s token from master (retry logic)
MAX_RETRIES=10
RETRY_COUNT=0
K3S_TOKEN=""

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    K3S_TOKEN=$(curl -s http://${master_private_ip}/k3s-token.txt 2>/dev/null || echo "")
    
    if [ -n "$K3S_TOKEN" ]; then
        echo "✓ Got k3s token from master"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Attempt $RETRY_COUNT/$MAX_RETRIES: Waiting for master..."
    sleep 30
done

if [ -z "$K3S_TOKEN" ]; then
    echo "❌ Failed to get k3s token from master"
    echo "Manual join required:"
    echo "  1. SSH to master and get token: sudo cat /var/lib/rancher/k3s/server/node-token"
    echo "  2. Run: curl -sfL https://get.k3s.io | K3S_URL=https://${master_private_ip}:6443 K3S_TOKEN=<token> sh -"
    exit 1
fi

# Install k3s agent
echo "Installing k3s agent..."
curl -sfL https://get.k3s.io | K3S_URL=https://${master_private_ip}:6443 K3S_TOKEN=$K3S_TOKEN sh -s - agent \
  --node-name worker

# Wait for k3s agent to be ready
sleep 30

# Verify k3s agent is running
systemctl status k3s-agent --no-pager

echo "========================================="
echo "Worker node setup complete!"
echo "========================================="
echo ""
echo "Verify on master:"
echo "  kubectl get nodes"
echo ""

# Save setup info
cat > /home/ubuntu/worker-info.txt <<EOF
Worker Node: $(hostname)
Master IP: ${master_private_ip}
k3s Version: $(k3s --version | head -n 1)
Setup Date: $(date)

Status: Connected to master
EOF

chown ubuntu:ubuntu /home/ubuntu/worker-info.txt

echo "Worker information saved to /home/ubuntu/worker-info.txt"
