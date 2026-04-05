# 🚀 AI SELF-HEALING PLATFORM - QUICK START GUIDE

**Complete Automated Deployment in 15 Minutes**

---

## ⚡ ONE-TIME SETUP (5 minutes)

### 1. Generate SSH Key
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/ai-healing-key
# Press Enter for all prompts (no passphrase)
```

### 2. Configure AWS Credentials
```bash
# Option A: Environment variables (PowerShell)
$env:AWS_ACCESS_KEY_ID="your-access-key-here"
$env:AWS_SECRET_ACCESS_KEY="your-secret-key-here"
$env:AWS_DEFAULT_REGION="us-east-1"

# Option B: AWS CLI
aws configure
```

### 3. Configure Terraform
```bash
# Copy example config
cp terraform.tfvars.example terraform.tfvars

# Edit - ONLY need to update SSH key paths
notepad terraform.tfvars  # Windows
nano terraform.tfvars     # Linux/Mac

# Change these two lines:
ssh_public_key_path  = "C:/Users/YourName/.ssh/ai-healing-key.pub"  # Windows
ssh_private_key_path = "C:/Users/YourName/.ssh/ai-healing-key"      # Windows

# Or for Linux/Mac:
ssh_public_key_path  = "/home/username/.ssh/ai-healing-key.pub"
ssh_private_key_path = "/home/username/.ssh/ai-healing-key"
```

---

## 🎯 DEPLOY (10 minutes)

```bash
# Step 1: Initialize Terraform (1 minute)
terraform init

# Step 2: Deploy (10 minutes - grab coffee ☕)
terraform apply
# Type 'yes' when prompted

# That's it! Wait for completion...
```

---

## ✅ ACCESS YOUR PLATFORM

After deployment completes, you'll see:

```
Outputs:

dashboard_url = "http://54.123.45.67:30800"
sample_app_url = "http://54.123.45.67:30080/health"
ssh_master_command = "ssh -i ~/.ssh/ai-healing-key ubuntu@54.123.45.67"
```

### Open Dashboard
```
http://54.123.45.67:30800  ← Copy this URL to your browser
```

**You should see:**
- ✅ Health Score: 100%
- ✅ Prometheus: Connected (green indicator)
- ✅ Kubernetes: Enabled (green indicator)
- ✅ ML Model: Trained (checkmark)
- ✅ Real-time graphs showing CPU, Memory, Latency

---

## 🧪 TEST SELF-HEALING (2 minutes)

### From PowerShell (Your Local Machine):
```powershell
# Replace with YOUR master IP from terraform output
.\load-test.ps1 -MasterIP "54.123.45.67" -TestType both
```

### Watch It Work:
1. Dashboard shows CPU spike
2. Anomaly detected automatically
3. Pods scale from 4 to 6+
4. System self-heals!

---

## 📊 VERIFY (SSH to Master)

```bash
# SSH to master
ssh -i ~/.ssh/ai-healing-key ubuntu@54.123.45.67

# Check cluster
sudo k3s kubectl get nodes
# Should show: master + worker = Ready

# Check pods
sudo k3s kubectl get pods -n monitoring-demo -o wide
# Should show 4+ pods distributed across both nodes

# Watch scaling in real-time
sudo k3s kubectl get hpa -n monitoring-demo -w
# After load test, should show CPU increase and replica scaling
```

---

## 🎓 FOR PRESENTATION

### Live Demo Script (10 minutes):

**1. Show Infrastructure (2 min)**
```bash
# Show Terraform outputs
terraform output

# SSH and show cluster
ssh -i ~/.ssh/ai-healing-key ubuntu@<master-ip>
sudo k3s kubectl get nodes
sudo k3s kubectl get pods -n monitoring-demo -o wide
```

**2. Show Dashboard (3 min)**
- Open `http://<master-ip>:30800`
- Explain each metric
- Show Prometheus connected
- Show ML model trained

**3. Trigger Self-Healing (5 min)**
```powershell
# Run from PowerShell
.\load-test.ps1 -MasterIP "<master-ip>" -TestType cpu
```

While running, show:
- Dashboard: CPU graph spiking
- SSH terminal: `kubectl get pods -w` (watch new pods appear)
- Dashboard: Anomaly detected
- Dashboard: Self-healing action logged

**4. Explain (2 min)**
- ML model detected CPU anomaly
- HPA automatically scaled pods
- Load distributed across master/worker
- No human intervention needed!

---

## 💰 COST & CLEANUP

### Current Cost:
- Worker (t3.micro): FREE (free tier)
- Master (t3.small): ~$0.02/hour = ~$15/month from $100 credit
- **Total: ~$15/month** (6+ months on free credit)

### Stop When Not In Use:
```bash
# AWS Console → EC2 → Select both instances → Stop
# (Free! Only pay for storage ~$2/month)

# Resume anytime: Start instances
```

### Complete Cleanup:
```bash
terraform destroy
# Type 'yes'
# Everything deleted in 3 minutes
```

---

## 🐛 TROUBLESHOOTING

### Dashboard Not Loading?
```bash
# SSH to master
ssh -i ~/.ssh/ai-healing-key ubuntu@<master-ip>

# Check if pods are running
sudo k3s kubectl get pods -n monitoring-demo

# Check service
sudo k3s kubectl get svc -n monitoring-demo

# Check logs
sudo k3s kubectl logs -l app=ai-platform -n monitoring-demo
```

### HPA Shows `<unknown>`?
```bash
# Wait 90 seconds, then check again
sleep 90
sudo k3s kubectl get hpa -n monitoring-demo

# Verify metrics-server
sudo k3s kubectl top nodes
```

### Pods Not Scaling?
```bash
# Check HPA
sudo k3s kubectl describe hpa sample-app -n monitoring-demo

# Run more aggressive load test
# Increase concurrent requests in load-test.ps1
```

---

## 📋 FILE STRUCTURE

```
ai-platform-terraform/
├── README.md                    ← Full documentation
├── DEPLOYMENT_CHECKLIST.md      ← Step-by-step checklist
├── QUICK_START.md              ← This file!
├── main.tf                      ← Terraform main config
├── variables.tf                 ← Terraform variables
├── outputs.tf                   ← Terraform outputs
├── terraform.tfvars.example     ← Config template
├── load-test.ps1               ← PowerShell load testing
├── .gitignore                   ← Git ignore rules
└── scripts/
    ├── master-init.sh           ← Master node setup
    ├── worker-init.sh           ← Worker node setup
    └── deploy-all.sh            ← Application deployment
```

---

## ✨ WHAT GETS DEPLOYED

### AWS Infrastructure:
- VPC with 2 subnets
- Internet Gateway
- Security Group (SSH, k3s, HTTP, NodePorts)
- 2 EC2 Instances (master + worker)
- SSH Key Pair

### Kubernetes Cluster:
- k3s (lightweight Kubernetes)
- Master node: Control plane + monitoring
- Worker node: Application workload
- metrics-server for HPA

### Applications:
- **AI Platform v17**: Anomaly detection, self-healing logic
- **Sample App**: Demo application with CPU/error endpoints
- **Prometheus**: Metrics collection
- **HPA**: Auto-scaling (4-10 pods, 60% CPU threshold)

### Services:
- Dashboard: Port 30800
- Sample App: Port 30080
- Prometheus: Port 30090

---

## 🎯 SUCCESS METRICS

Your deployment is successful when:

- [x] `terraform apply` completes without errors
- [x] Dashboard loads in browser
- [x] Health score = 100%
- [x] 4 pods running across both nodes
- [x] HPA shows `cpu: X%/60%`
- [x] Load test triggers scaling (4 → 6+ pods)
- [x] Anomalies auto-detected
- [x] Self-healing actions logged

---

## 🆘 NEED HELP?

1. Check `README.md` for detailed troubleshooting
2. Check `DEPLOYMENT_CHECKLIST.md` for step-by-step validation
3. SSH to master and check logs: `kubectl logs -n monitoring-demo`
4. Verify AWS Console shows both instances running
5. Test connectivity: `curl http://localhost:30800/api/v1/status` (from master)

---

**TOTAL TIME: ~15 minutes from start to working demo**

**Perfect for:**
- MTech project demonstration
- Understanding Kubernetes auto-scaling
- Learning Terraform automation
- Showcasing AI/ML in DevOps

**Good luck with your presentation! 🚀**
