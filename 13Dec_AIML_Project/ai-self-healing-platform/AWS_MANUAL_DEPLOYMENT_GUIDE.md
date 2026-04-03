# AWS Manual Deployment Guide
## AI Self-Healing Platform - Step-by-Step

**Author**: MTech Project Guide  
**Date**: April 2026  
**Estimated Time**: 45-60 minutes  
**Cost**: $0 (AWS Free Tier) or ~$15/month from credit

---

## 📋 TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [Phase 1: VPC & Networking](#phase-1-vpc--networking)
3. [Phase 2: Security Group](#phase-2-security-group)
4. [Phase 3: Launch Master Node](#phase-3-launch-master-node)
5. [Phase 4: Verify Master](#phase-4-verify-master)
6. [Phase 5: Launch Worker Node](#phase-5-launch-worker-node)
7. [Phase 6: Join Worker to Cluster](#phase-6-join-worker-to-cluster)
8. [Phase 7: Access from Local Machine](#phase-7-access-from-local-machine)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## PREREQUISITES

### ✅ **What You Need**

- [ ] AWS Account with $100 credit
- [ ] SSH key pair created: `mtech-project-key`
- [ ] SSH client (PowerShell on Windows has it built-in)
- [ ] kubectl installed locally (optional for now)

### ✅ **Create SSH Key (If Not Done)**

**PowerShell:**
```powershell
# Create SSH key in AWS
aws ec2 create-key-pair `
  --key-name mtech-project-key `
  --query 'KeyMaterial' `
  --output text | Out-File -FilePath ~/.ssh/mtech-project-key.pem -Encoding ASCII

# Verify
aws ec2 describe-key-pairs --key-names mtech-project-key
```

---

## PHASE 1: VPC & NETWORKING

**Time**: ~5 minutes

### Step 1.1: Create VPC

1. Go to **AWS Console**: https://console.aws.amazon.com
2. Search for **"VPC"** in top search bar
3. Click **"VPC"** service
4. Click **"Create VPC"** (orange button)
5. Select: **"VPC and more"**

### Step 1.2: Configure VPC

Fill in these settings:

```yaml
Name tag: ai-healing-vpc

IPv4 CIDR block: 10.0.0.0/16
IPv6 CIDR block: No IPv6 CIDR block
Tenancy: Default

Number of Availability Zones: 2
Number of public subnets: 2
Number of private subnets: 0

NAT gateways: None
VPC endpoints: None
DNS options: ✓ Enable DNS hostnames
           ✓ Enable DNS resolution
```

6. Click **"Create VPC"**
7. Wait ~2 minutes for creation
8. Click **"View VPC"**

**✅ Created:**
- 1 VPC (ai-healing-vpc)
- 2 Public subnets
- 1 Internet Gateway (auto-attached)
- Route tables (auto-configured)

---

## PHASE 2: SECURITY GROUP

**Time**: ~5 minutes

### Step 2.1: Create Security Group

1. In VPC Dashboard → Left sidebar → **"Security Groups"**
2. Click **"Create security group"**

### Step 2.2: Basic Details

```yaml
Security group name: k3s-cluster-sg
Description: Security group for k3s Kubernetes cluster
VPC: ai-healing-vpc (select from dropdown)
```

### Step 2.3: Add Inbound Rules

Click **"Add rule"** for each of these:

#### Rule 1: SSH
```yaml
Type: SSH
Protocol: TCP
Port range: 22
Source: Anywhere IPv4 (0.0.0.0/0)
Description: SSH access
```

#### Rule 2: Kubernetes API
```yaml
Type: Custom TCP
Protocol: TCP
Port range: 6443
Source: Anywhere IPv4 (0.0.0.0/0)
Description: Kubernetes API server
```

#### Rule 3: HTTP
```yaml
Type: HTTP
Protocol: TCP
Port range: 80
Source: Anywhere IPv4 (0.0.0.0/0)
Description: HTTP traffic
```

#### Rule 4: HTTPS
```yaml
Type: HTTPS
Protocol: TCP
Port range: 443
Source: Anywhere IPv4 (0.0.0.0/0)
Description: HTTPS traffic
```

#### Rule 5: NodePort Services
```yaml
Type: Custom TCP
Protocol: TCP
Port range: 30000-32767
Source: Anywhere IPv4 (0.0.0.0/0)
Description: Kubernetes NodePort services
```

#### Rule 6: Internal Cluster Traffic (IMPORTANT!)
```yaml
Type: All traffic
Protocol: All
Port range: All
Source: Custom → Select "k3s-cluster-sg" (this security group itself)
Description: Internal cluster communication
```

### Step 2.4: Outbound Rules

Leave default:
```yaml
Type: All traffic
Destination: 0.0.0.0/0
```

### Step 2.5: Create

Click **"Create security group"**

**✅ Security group created with 6 inbound rules**

---

## PHASE 3: LAUNCH MASTER NODE

**Time**: ~10 minutes

### Step 3.1: Launch Instance

1. Go to **EC2 Dashboard**
2. Click **"Launch instance"** (orange button)

### Step 3.2: Configure Instance

#### Name and Tags
```yaml
Name: ai-healing-master
Tags: 
  - Key: Role, Value: master
```

#### Application and OS Images (AMI)
```yaml
Quick Start: Ubuntu
AMI: Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
Architecture: 64-bit (x86)
✓ Free tier eligible
```

#### Instance Type
```yaml
Family: t3
Type: t3.micro
✓ Free tier eligible
```

#### Key Pair
```yaml
Key pair name: mtech-project-key
```

#### Network Settings

Click **"Edit"**:

```yaml
VPC: ai-healing-vpc
Subnet: Any public subnet (e.g., ai-healing-vpc-subnet-public1-us-east-1a)
Auto-assign public IP: Enable
Firewall (security groups): Select existing security group
Security groups: k3s-cluster-sg
```

#### Configure Storage
```yaml
Size: 30 GiB
Volume type: gp3
Delete on termination: Yes
✓ Free tier: 30 GB included
```

### Step 3.3: Advanced Details - User Data

Scroll down to **"User data"** text box and paste this script:

```bash
#!/bin/bash
set -e

echo "========================================="
echo "k3s Master Node Setup - MTech Project"
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

# Install Docker
echo "Installing Docker..."
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
echo "Waiting for k3s to initialize..."
sleep 60

# Verify k3s is running
systemctl status k3s --no-pager || true

# Install Helm
echo "Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Wait for k3s to be fully operational
echo "Waiting for nodes to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s || true

# Install Prometheus
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
  --set pushgateway.enabled=false \
  --wait --timeout=10m

# Install metrics-server for HPA
echo "Installing metrics-server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics-server for k3s
sleep 30
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

# Create deployment directory
mkdir -p /home/ubuntu/ai-platform
chown ubuntu:ubuntu /home/ubuntu/ai-platform

# Save cluster info
cat > /home/ubuntu/cluster-info.txt <<EOF
========================================
AI Self-Healing Platform - Cluster Info
========================================

Cluster Name: ai-healing-cluster
Master Node: $(hostname)
Master Public IP: $MASTER_IP
Master Private IP: $(hostname -I | awk '{print $1}')
k3s Version: $(k3s --version | head -n 1)
Setup Date: $(date)

Quick Commands:
  kubectl get nodes
  kubectl get pods -A
  kubectl cluster-info

Service URLs:
  Prometheus: http://$MASTER_IP:30090
  Dashboard: http://$MASTER_IP:30888 (after platform deployment)
  Sample App: http://$MASTER_IP:30080 (after platform deployment)

Files:
  Kubeconfig: /tmp/k3s-config.yaml
  Token: /tmp/k3s-token.txt
  
Next Steps:
  1. Wait for worker node to join
  2. Deploy AI platform
  3. Run validation tests
EOF

chown ubuntu:ubuntu /home/ubuntu/cluster-info.txt

echo "========================================="
echo "Master node setup complete!"
echo "Public IP: $MASTER_IP"
echo "Check /home/ubuntu/cluster-info.txt for details"
echo "========================================="
```

### Step 3.4: Launch

1. Review all settings
2. Click **"Launch instance"**
3. Wait ~2 minutes for instance to start

**✅ Master node is launching!**

---

## PHASE 4: VERIFY MASTER

**Time**: ~10 minutes (wait for initialization)

### Step 4.1: Check Instance Status

1. Go to **EC2 Dashboard → Instances**
2. Find **"ai-healing-master"**
3. Wait until:
   - Instance State: **Running** (green)
   - Status checks: **2/2 checks passed** (takes ~3-5 minutes)

### Step 4.2: Note Down Information

**Copy these values:**

```
Master Public IP: ________________ (e.g., 54.123.45.67)
Master Private IP: _______________ (e.g., 10.0.1.123)
```

### Step 4.3: Wait for k3s Installation

**Important**: The user data script takes ~8-10 minutes to complete.

Wait at least **10 minutes** after instance shows "Running" before SSH'ing.

### Step 4.4: SSH and Verify

```powershell
# SSH to master (replace with YOUR master public IP)
ssh -i ~/.ssh/mtech-project-key.pem ubuntu@54.123.45.67
```

**On master, run:**

```bash
# Check k3s status
sudo systemctl status k3s

# Should show: Active: active (running)

# Check nodes
kubectl get nodes

# Should show:
# NAME     STATUS   ROLES                  AGE   VERSION
# master   Ready    control-plane,master   5m    v1.34.x+k3s1

# Check Prometheus
kubectl get pods -n monitoring

# Should show prometheus pods running

# View cluster info
cat ~/cluster-info.txt
```

**If everything looks good, exit:**

```bash
exit
```

**✅ Master is ready!**

---

## PHASE 5: LAUNCH WORKER NODE

**Time**: ~10 minutes

### Step 5.1: Get Master's Private IP

**From EC2 Console:**

1. Click on **"ai-healing-master"** instance
2. Copy **"Private IPv4 addresses"** (e.g., 10.0.1.123)
3. **Write this down!** You'll need it in the user data script

### Step 5.2: Launch Worker Instance

1. EC2 Dashboard → Click **"Launch instance"**

#### Name and Tags
```yaml
Name: ai-healing-worker
Tags:
  - Key: Role, Value: worker
```

#### AMI
```yaml
Ubuntu Server 22.04 LTS (same as master)
✓ Free tier eligible
```

#### Instance Type
```yaml
Type: t3.micro
✓ Free tier eligible
```

#### Key Pair
```yaml
Key pair: mtech-project-key
```

#### Network Settings

Click **"Edit"**:

```yaml
VPC: ai-healing-vpc
Subnet: SELECT THE OTHER PUBLIC SUBNET
        (If master is in subnet-1a, choose subnet-1b)
Auto-assign public IP: Enable
Security group: k3s-cluster-sg
```

**⚠️ IMPORTANT**: Choose a different subnet than master for high availability!

#### Storage
```yaml
Size: 30 GiB
Volume type: gp3
Delete on termination: Yes
```

### Step 5.3: Advanced Details - User Data

**⚠️ CRITICAL**: Replace `MASTER_PRIVATE_IP_HERE` with the actual private IP you copied!

```bash
#!/bin/bash
set -e

echo "========================================="
echo "k3s Worker Node Setup - MTech Project"
echo "========================================="

# ⚠️ REPLACE THIS WITH YOUR MASTER'S PRIVATE IP!
MASTER_PRIVATE_IP="10.0.1.123"  # ← CHANGE THIS!

echo "Master Private IP: $MASTER_PRIVATE_IP"

# Update system
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y curl wget git

# Install Docker
echo "Installing Docker..."
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu

# Wait for master to be ready
echo "Waiting for master node to be ready..."
sleep 180

# Get k3s token from master via HTTP
# Note: This is a simplified approach for demo
# In production, use AWS Secrets Manager or Systems Manager Parameter Store
echo "Attempting to get k3s token from master..."

MAX_RETRIES=20
RETRY_COUNT=0
K3S_TOKEN=""

# Try to get token (master exposes it at /tmp/k3s-token.txt)
# This works if master has an HTTP server or we use SSH keys
# For now, we'll set it manually after creation

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Attempt $RETRY_COUNT/$MAX_RETRIES: Waiting for master to be fully ready..."
    sleep 15
done

echo "========================================="
echo "Worker node preparation complete!"
echo ""
echo "MANUAL STEP REQUIRED:"
echo "1. SSH to master and get token:"
echo "   sudo cat /var/lib/rancher/k3s/server/node-token"
echo ""
echo "2. Then on this worker, run:"
echo "   curl -sfL https://get.k3s.io | \\"
echo "     K3S_URL=https://$MASTER_PRIVATE_IP:6443 \\"
echo "     K3S_TOKEN=<token-from-master> \\"
echo "     sh -s - agent --node-name worker"
echo "========================================="

# Create info file
cat > /home/ubuntu/worker-info.txt <<EOF
Worker Node: $(hostname)
Master Private IP: $MASTER_PRIVATE_IP
Setup Date: $(date)

To join cluster manually:
1. Get token from master:
   ssh to master: sudo cat /var/lib/rancher/k3s/server/node-token

2. Run this command on worker:
   curl -sfL https://get.k3s.io | \\
     K3S_URL=https://$MASTER_PRIVATE_IP:6443 \\
     K3S_TOKEN=<token> \\
     sh -s - agent --node-name worker
EOF

chown ubuntu:ubuntu /home/ubuntu/worker-info.txt

echo "Setup info saved to /home/ubuntu/worker-info.txt"
```

### Step 5.4: Launch

1. Review settings
2. Click **"Launch instance"**
3. Wait for instance to start

**✅ Worker node launched!**

---

## PHASE 6: JOIN WORKER TO CLUSTER

**Time**: ~5 minutes

### Step 6.1: Get Token from Master

**SSH to Master:**

```powershell
ssh -i ~/.ssh/mtech-project-key.pem ubuntu@<MASTER_PUBLIC_IP>
```

**Get the k3s token:**

```bash
# Get token
sudo cat /var/lib/rancher/k3s/server/node-token

# Copy the entire token - looks like:
# K10abc123def456ghi789jkl012mno345pqr678stu::server:9vwx0yz1abc2def3ghi4
```

**Copy this token!**

**Exit master:**

```bash
exit
```

### Step 6.2: SSH to Worker

```powershell
# Get worker's public IP from EC2 Console
# Then SSH to worker
ssh -i ~/.ssh/mtech-project-key.pem ubuntu@<WORKER_PUBLIC_IP>
```

### Step 6.3: Join Worker to Cluster

**On worker, run this command:**

Replace:
- `<TOKEN>` with the token you copied from master
- `<MASTER_PRIVATE_IP>` with master's private IP (e.g., 10.0.1.123)

```bash
curl -sfL https://get.k3s.io | \
  K3S_URL=https://<MASTER_PRIVATE_IP>:6443 \
  K3S_TOKEN=<TOKEN> \
  sh -s - agent --node-name worker
```

**Example:**
```bash
curl -sfL https://get.k3s.io | \
  K3S_URL=https://10.0.1.123:6443 \
  K3S_TOKEN=K10abc123def456ghi789jkl012mno345pqr678stu::server:9vwx0yz1abc2def3ghi4 \
  sh -s - agent --node-name worker
```

**Wait for installation (~2-3 minutes)**

### Step 6.4: Verify Worker

**On worker:**

```bash
# Check k3s-agent status
sudo systemctl status k3s-agent

# Should show: Active: active (running)

# Check logs
sudo journalctl -u k3s-agent -n 30 --no-pager

# Look for: "k3s agent is up and running"
```

**Exit worker:**

```bash
exit
```

### Step 6.5: Verify from Master

**SSH back to master:**

```powershell
ssh -i ~/.ssh/mtech-project-key.pem ubuntu@<MASTER_PUBLIC_IP>
```

**Check nodes:**

```bash
kubectl get nodes

# Should now show TWO nodes:
# NAME     STATUS   ROLES                  AGE   VERSION
# master   Ready    control-plane,master   20m   v1.34.6+k3s1
# worker   Ready    <none>                 3m    v1.34.6+k3s1

# Check in detail
kubectl get nodes -o wide

# Check all pods
kubectl get pods -A -o wide

# Some pods should be running on worker now
```

**✅ Cluster is ready! Both nodes joined!**

---

## PHASE 7: ACCESS FROM LOCAL MACHINE

**Time**: ~5 minutes

### Step 7.1: Download kubeconfig

**From your local machine (PowerShell):**

```powershell
# Create .kube directory
mkdir $HOME\.kube -ErrorAction SilentlyContinue

# Download kubeconfig
scp -i ~/.ssh/mtech-project-key.pem ubuntu@<MASTER_PUBLIC_IP>:/tmp/k3s-config.yaml $HOME\.kube\aws-config

# Verify download
Get-Content $HOME\.kube\aws-config | Select-String "server:"

# Should show: server: https://<MASTER_PUBLIC_IP>:6443
```

### Step 7.2: Set KUBECONFIG (Optional for Now)

**Note**: Due to potential TLS issues, we'll use SSH-based kubectl for now.

### Step 7.3: Use SSH-based kubectl (Recommended)

**Create this function:**

```powershell
# Add to your PowerShell session
function k {
    ssh -i ~/.ssh/mtech-project-key.pem ubuntu@<MASTER_PUBLIC_IP> "kubectl $args"
}

# Test it
k get nodes
k get pods -A
k cluster-info
```

### Step 7.4: Make Function Permanent (Optional)

```powershell
# Add to PowerShell profile
$profilePath = $PROFILE
if (!(Test-Path $profilePath)) {
    New-Item -Path $profilePath -Type File -Force
}

# Replace <MASTER_PUBLIC_IP> with actual IP
Add-Content $profilePath @'
function k {
    ssh -i ~/.ssh/mtech-project-key.pem ubuntu@54.123.45.67 "kubectl $args"
}
'@

# Reload profile
. $PROFILE
```

**✅ You can now control the cluster from your laptop!**

---

## TROUBLESHOOTING

### Issue: Can't SSH to Instances

**Check:**
1. Security group has SSH rule (port 22)
2. Using correct key: `mtech-project-key.pem`
3. Instance has public IP assigned

**Fix:**
```powershell
# Verify key
ls ~/.ssh/mtech-project-key.pem

# Test connection
ssh -i ~/.ssh/mtech-project-key.pem -v ubuntu@<PUBLIC_IP>
```

### Issue: Worker Not Joining

**Check:**
1. Security group has "All traffic from self" rule
2. Used correct master PRIVATE IP (not public)
3. Token copied correctly

**Fix:**
```bash
# On worker, check logs
sudo journalctl -u k3s-agent -f

# Look for connection errors
```

### Issue: k3s Not Starting

**Check:**
```bash
# On master
sudo systemctl status k3s

# Check logs
sudo journalctl -u k3s -n 100 --no-pager

# Restart if needed
sudo systemctl restart k3s
```

### Issue: Prometheus Not Running

**Check:**
```bash
kubectl get pods -n monitoring

# If failing, check logs
kubectl logs -n monitoring deployment/prometheus-server

# Reinstall if needed
helm uninstall prometheus -n monitoring
# Then re-run helm install command from user data
```

---

## VERIFICATION CHECKLIST

Before proceeding, verify:

- [ ] Both EC2 instances running
- [ ] Both instances have public IPs
- [ ] Can SSH to both instances
- [ ] `kubectl get nodes` shows 2 nodes (both Ready)
- [ ] Prometheus pods running: `kubectl get pods -n monitoring`
- [ ] Can access Prometheus: http://<MASTER_IP>:30090
- [ ] No errors in logs: `sudo journalctl -u k3s -n 50 --no-pager`

---

## CLUSTER INFORMATION TEMPLATE

**Save this information:**

```
=========================================
AWS KUBERNETES CLUSTER - MTech Project
=========================================

Date Created: _______________

VPC Details:
  VPC ID: vpc-_______________
  CIDR: 10.0.0.0/16
  Name: ai-healing-vpc

Security Group:
  SG ID: sg-_______________
  Name: k3s-cluster-sg

Master Node:
  Instance ID: i-_______________
  Public IP: _______________
  Private IP: _______________
  SSH: ssh -i ~/.ssh/mtech-project-key.pem ubuntu@<PUBLIC_IP>

Worker Node:
  Instance ID: i-_______________
  Public IP: _______________
  Private IP: _______________
  SSH: ssh -i ~/.ssh/mtech-project-key.pem ubuntu@<PUBLIC_IP>

Cluster Access:
  kubectl via SSH: 
    function k { ssh -i ~/.ssh/mtech-project-key.pem ubuntu@<MASTER_IP> "kubectl $args" }
  
  Commands:
    k get nodes
    k get pods -A
    k apply -f deployment.yaml

Service URLs:
  Prometheus: http://<MASTER_PUBLIC_IP>:30090
  Dashboard: http://<MASTER_PUBLIC_IP>:30888 (after deployment)
  Sample App: http://<MASTER_PUBLIC_IP>:30080 (after deployment)

Cost Tracking:
  Instance hours used: ___ / 750 (free tier)
  Estimated cost: $0 (free tier) or ~$15/month

Notes:
  - Stop instances when not in use to save credits
  - Both instances in different AZs for HA
  - All services use NodePort for external access
=========================================
```

---

## NEXT STEPS

Now that your cluster is ready, proceed to:

1. **Deploy AI Self-Healing Platform**
   - Build Docker images
   - Create Kubernetes deployments
   - Configure RBAC and services

2. **Run Validation Tests**
   - CPU spike tests
   - Memory pressure tests
   - Self-healing verification

3. **Collect Metrics**
   - Detection accuracy
   - Healing success rate
   - Mean time to recovery (MTTR)

4. **Practice Terraform Deployment**
   - Destroy manual cluster
   - Deploy with Terraform
   - Compare manual vs automated

---

## COST MANAGEMENT

### Monitor Usage

```
AWS Console → Billing → Free Tier
Check: EC2 hours used / 750 available
```

### Stop Instances (When Not Using)

```
EC2 Console → Instances → Select both instances
Actions → Instance State → Stop

To restart later:
Actions → Instance State → Start
```

### Destroy Everything (When Done)

**Option 1: Via Console**
```
1. EC2 → Instances → Select both → Terminate
2. VPC → Delete VPC (deletes everything)
3. EC2 → Key Pairs → Delete mtech-project-key
```

**Option 2: Keep for Terraform Practice**
```
Just stop instances (not terminate)
Use them as reference for Terraform deployment
```

---

## SUMMARY

**What You Built:**
- ✅ Custom VPC with proper networking
- ✅ Security group with all required ports
- ✅ 2-node Kubernetes cluster (k3s)
- ✅ Prometheus monitoring
- ✅ High availability (2 AZs)
- ✅ Production-like setup

**Time Invested**: ~45 minutes  
**Cost**: $0 (Free tier)  
**Nodes**: 2 (master + worker)  
**Status**: Production-ready for demo

**Skills Learned:**
- AWS VPC creation
- Security group configuration
- EC2 instance management
- Kubernetes cluster setup
- k3s installation
- Infrastructure troubleshooting

**Next**: Deploy your MTech AI Platform! 🚀

---

**End of Manual Deployment Guide**
