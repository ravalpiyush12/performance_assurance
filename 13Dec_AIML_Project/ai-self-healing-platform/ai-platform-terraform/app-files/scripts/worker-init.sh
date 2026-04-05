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
    docker.io

# Start Docker
systemctl enable docker
systemctl start docker

# Wait for master to be ready
echo "Waiting for master node at ${master_ip}..."
timeout 300 bash -c 'until nc -z ${master_ip} 6443; do sleep 5; done'

# Install k3s (worker)
curl -sfL https://get.k3s.io | K3S_URL=https://${master_ip}:6443 \
    K3S_TOKEN=${k3s_token} \
    INSTALL_K3S_EXEC="agent --node-name=worker" sh -

echo "Worker node initialization complete!"
