# AI Self-Healing Platform - Terraform Automated Deployment

**MTech Project: AI/ML-Driven Intelligent Performance Assurance and Self-Healing Platform for Cloud Workloads**

This Terraform configuration automatically deploys a complete AI self-healing platform on AWS with:
- k3s Kubernetes cluster (master + worker nodes)
- Prometheus monitoring
- AI/ML anomaly detection
- Automated self-healing with HPA
- Multi-node workload distribution

---

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with:
   - Valid credentials configured
   - $100 credit or free tier available
   - IAM permissions for EC2, VPC, Security Groups

2. **Local Tools**:
   ```bash
   # Install Terraform
   # Windows (PowerShell as Admin):
   choco install terraform
   
   # Linux:
   sudo apt-get install terraform
   
   # Verify
   terraform version
   ```

3. **SSH Key Pair**:
   ```bash
   # Generate new SSH key
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/ai-healing-key
   
   # This creates:
   # ~/.ssh/ai-healing-key (private)
   # ~/.ssh/ai-healing-key.pub (public)
   ```

---

## 📋 Deployment Steps

### Step 1: Configure AWS Credentials

```bash
# Option 1: Environment Variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Option 2: AWS CLI
aws configure
```

### Step 2: Configure Terraform

```bash
# Copy example config
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars
nano terraform.tfvars
```

**Minimum Required Changes:**
```hcl
# Update SSH key paths
ssh_public_key_path  = "~/.ssh/ai-healing-key.pub"
ssh_private_key_path = "~/.ssh/ai-healing-key"

# Optional: Change k3s token for security
k3s_token = "your-unique-secure-token-here"
```

### Step 3: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review deployment plan
terraform plan

# Deploy (takes 5-10 minutes)
terraform apply

# Type 'yes' when prompted
```

### Step 4: Access Your Platform

After successful deployment, Terraform outputs:

```
Outputs:

dashboard_url = "http://54.XXX.XXX.XXX:30800"
sample_app_url = "http://54.XXX.XXX.XXX:30080/health"
prometheus_url = "http://54.XXX.XXX.XXX:30090"
ssh_master_command = "ssh -i ~/.ssh/ai-healing-key ubuntu@54.XXX.XXX.XXX"
```

**Open dashboard in browser:**
```
http://<master-ip>:30800
```

You should see:
- ✅ Health Score: 100%
- ✅ Prometheus: Connected
- ✅ Kubernetes: Enabled
- ✅ ML Model: Trained
- ✅ Real-time metrics graphs

---

## 🧪 Testing Self-Healing

### Method 1: PowerShell Load Test (Recommended)

```powershell
# Run from your local machine
.\load-test.ps1 -MasterIP "54.XXX.XXX.XXX" -TestType both
```

### Method 2: Manual Testing

```powershell
$IP = "54.XXX.XXX.XXX"

# Generate CPU load
for ($i = 1; $i -le 50; $i++) {
    Invoke-WebRequest -Uri "http://${IP}:30080/compute" -UseBasicParsing
}

# Generate errors
for ($i = 1; $i -le 20; $i++) {
    Invoke-WebRequest -Uri "http://${IP}:30080/error" -ErrorAction SilentlyContinue
}
```

### Method 3: SSH and Monitor

```bash
# SSH to master
ssh -i ~/.ssh/ai-healing-key ubuntu@<master-ip>

# Watch HPA scaling
sudo k3s kubectl get hpa -n monitoring-demo -w

# Watch pods scaling
sudo k3s kubectl get pods -n monitoring-demo -w

# Check metrics
sudo k3s kubectl top nodes
sudo k3s kubectl top pods -n monitoring-demo
```

---

## 📊 Expected Results

After load testing, you should observe:

### Dashboard Changes:
1. **CPU Usage Graph**: Spike from ~10% to 60-80%
2. **Recent Anomalies**: New `CPU_USAGE` anomaly (critical severity)
3. **Self-Healing Actions**: Actions logged showing pod scaling
4. **Active Alerts**: Alert count increases during high load
5. **Error Rate Graph**: Populated with error data

### Kubernetes Changes:
```bash
# Before load test
NAME                           READY   STATUS    NODE
sample-app-xxxxx-xxxxx         1/1     Running   master
sample-app-xxxxx-xxxxx         1/1     Running   worker
sample-app-xxxxx-xxxxx         1/1     Running   master
sample-app-xxxxx-xxxxx         1/1     Running   worker

# During/after load test (HPA scaling)
NAME                           READY   STATUS    NODE
sample-app-xxxxx-xxxxx         1/1     Running   master
sample-app-xxxxx-xxxxx         1/1     Running   worker
sample-app-xxxxx-xxxxx         1/1     Running   master
sample-app-xxxxx-xxxxx         1/1     Running   worker
sample-app-xxxxx-xxxxx         1/1     Running   master  ← New
sample-app-xxxxx-xxxxx         1/1     Running   worker  ← New
```

### HPA Activity:
```
NAME         REFERENCE               TARGETS        MINPODS   MAXPODS   REPLICAS
sample-app   Deployment/sample-app   cpu: 75%/60%   4         10        6
```

---

## 🔍 Troubleshooting

### Check Deployment Status

```bash
# SSH to master
ssh -i ~/.ssh/ai-healing-key ubuntu@<master-ip>

# Check all pods
sudo k3s kubectl get pods -A

# Check monitoring-demo namespace
sudo k3s kubectl get pods -n monitoring-demo -o wide

# Check logs
sudo k3s kubectl logs -l app=ai-platform -n monitoring-demo --tail=50
```

### Common Issues

**Issue: Dashboard not accessible**
```bash
# Check if service is running
sudo k3s kubectl get svc -n monitoring-demo

# Check pod status
sudo k3s kubectl get pods -n monitoring-demo

# Check logs
sudo k3s kubectl logs -l app=ai-platform -n monitoring-demo
```

**Issue: HPA shows `<unknown>`**
```bash
# Wait 60-90 seconds for metrics to populate
sleep 90
sudo k3s kubectl get hpa -n monitoring-demo

# Check metrics-server
sudo k3s kubectl top nodes
sudo k3s kubectl top pods -n monitoring-demo
```

**Issue: Pods not distributed**
```bash
# Check node labels
sudo k3s kubectl get nodes --show-labels

# Check pod distribution
sudo k3s kubectl get pods -n monitoring-demo -o wide
```

---

## 💰 Cost Management

### Free Tier Usage
- **t3.micro worker**: 750 hours/month FREE (12 months)
- **t3.small master**: ~$15/month from $100 credit (~6 months)
- **Storage**: Minimal (20GB each = $2/month)
- **Network**: Minimal for demo usage

### Stop Instances When Not In Use
```bash
# Via Terraform
terraform destroy

# Via AWS Console
EC2 → Instances → Select both → Instance State → Stop
```

### Monitor Costs
```bash
# AWS CLI
aws ce get-cost-and-usage \
    --time-period Start=2026-04-01,End=2026-04-30 \
    --granularity MONTHLY \
    --metrics BlendedCost
```

---

## 📁 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AWS VPC (10.0.0.0/16)                   │
│                                                              │
│  ┌────────────────────────┐    ┌────────────────────────┐  │
│  │   Public Subnet 1      │    │   Public Subnet 2      │  │
│  │                        │    │                        │  │
│  │  ┌─────────────────┐  │    │  ┌─────────────────┐  │  │
│  │  │ Master Node     │  │    │  │ Worker Node     │  │  │
│  │  │ (t3.small)      │  │    │  │ (t3.micro)      │  │  │
│  │  │                 │  │    │  │                 │  │  │
│  │  │ • k3s Control   │◄─┼────┼─►│ • k3s Agent     │  │  │
│  │  │ • AI Platform   │  │    │  │ • Sample App    │  │  │
│  │  │ • Prometheus    │  │    │  │   (2+ pods)     │  │  │
│  │  │ • Sample App    │  │    │  │                 │  │  │
│  │  │   (2 pods)      │  │    │  │                 │  │  │
│  │  └─────────────────┘  │    │  └─────────────────┘  │  │
│  │         │              │    │         │              │  │
│  └─────────┼──────────────┘    └─────────┼──────────────┘  │
│            │                              │                  │
│  ┌─────────▼──────────────────────────────▼────────────┐   │
│  │           Internet Gateway                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
                     Internet Access
                  (Dashboard, SSH, APIs)
```

### Components:
- **Master Node**: k3s control plane, AI platform, Prometheus, metrics-server
- **Worker Node**: Application workload (sample-app pods)
- **HPA**: Auto-scales sample-app from 4 to 10 pods based on CPU
- **Prometheus**: Scrapes metrics every 15 seconds
- **Services**: NodePort (30080, 30800, 30090) for external access

---

## 🛠️ Maintenance

### Update Application Code
```bash
# SSH to master
ssh -i ~/.ssh/ai-healing-key ubuntu@<master-ip>

# Edit application files
cd /home/ubuntu/ai-platform
nano ai-platform.py

# Rebuild and redeploy
sudo docker build -t ai-platform:v17 -f Dockerfile.platform .
sudo docker save ai-platform:v17 | sudo k3s ctr images import -

# Restart pods
sudo k3s kubectl rollout restart deployment/ai-platform -n monitoring-demo
```

### View Logs
```bash
# AI Platform logs
sudo k3s kubectl logs -l app=ai-platform -n monitoring-demo --tail=100 -f

# Sample App logs
sudo k3s kubectl logs -l app=sample-app -n monitoring-demo --tail=50

# Prometheus logs
sudo k3s kubectl logs -l app=prometheus-server -n monitoring --tail=50
```

### Scale Manually
```bash
# Scale sample-app
sudo k3s kubectl scale deployment sample-app -n monitoring-demo --replicas=6

# Check scaling
sudo k3s kubectl get pods -n monitoring-demo -o wide
```

---

## 🎓 For MTech Presentation

### Demo Script:

1. **Show Infrastructure** (2 mins)
   - Terraform outputs
   - AWS Console (EC2 instances)
   - SSH to master, show `kubectl get nodes`

2. **Show Dashboard** (3 mins)
   - Open http://<master-ip>:30800
   - Explain metrics: CPU, memory, latency, errors
   - Show Prometheus connected, ML trained

3. **Trigger Self-Healing** (5 mins)
   - Run `load-test.ps1` from PowerShell
   - Watch dashboard: CPU spikes
   - Show anomaly detection
   - Watch pods scaling: `kubectl get pods -w`
   - Show HPA activity: `kubectl get hpa -w`

4. **Explain Results** (3 mins)
   - Anomaly detected automatically
   - HPA triggered pod scaling
   - Load distributed across nodes
   - System self-healed without human intervention

---

## 📝 Cleanup

```bash
# Destroy all infrastructure
terraform destroy

# Type 'yes' when prompted

# Verify in AWS Console that all resources are deleted
```

---

## 📚 Documentation

- **Terraform Files**: `main.tf`, `variables.tf`, `outputs.tf`
- **Scripts**: `scripts/master-init.sh`, `scripts/worker-init.sh`, `scripts/deploy-all.sh`
- **Load Testing**: `load-test.ps1`
- **Kubernetes Manifests**: Auto-generated in `~/ai-platform/kubernetes/` on master

---

## ✅ Success Criteria

Your deployment is successful when:

- [x] `terraform apply` completes without errors
- [x] Dashboard accessible at `http://<master-ip>:30800`
- [x] Health score shows 100%
- [x] Prometheus status: Connected (green)
- [x] ML Model: Trained (checkmark)
- [x] 4 sample-app pods running (distributed across nodes)
- [x] HPA shows `cpu: X%/60%`
- [x] Load test triggers pod scaling (4 → 6+ pods)
- [x] Anomalies detected and displayed
- [x] Self-healing actions logged

---

## 🎉 Expected Timeline

- Terraform init: 1 minute
- Terraform apply: 8-12 minutes
  - VPC/networking: 2 min
  - EC2 instances: 2 min
  - k3s installation: 3 min
  - Application deployment: 3 min
  - HPA initialization: 2 min
- Load testing: 2 minutes
- **Total: ~15 minutes** from `terraform apply` to working demo

---

**For Questions or Issues:**
- Check logs: `sudo k3s kubectl logs -n monitoring-demo`
- Verify connectivity: `curl http://localhost:30800/api/v1/status`
- SSH debug: `ssh -i ~/.ssh/ai-healing-key -v ubuntu@<master-ip>`

**Project**: MTech IIT Patna - AI Self-Healing Platform
**Author**: Piyush Raval
**Version**: v17 (Automated Terraform Deployment)
