# 🚀 AI SELF-HEALING PLATFORM - QUICK REFERENCE CARD

## 📥 SETUP (One-Time)

```bash
# 1. Extract archive
unzip ai-platform-terraform.zip
cd ai-platform-terraform

# 2. Generate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/ai-healing-key

# 3. Configure AWS
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# 4. Configure Terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
# Update: ssh_public_key_path and ssh_private_key_path
```

---

## 🚀 DEPLOY

```bash
terraform init          # Initialize (1 min)
terraform plan          # Review changes
terraform apply         # Deploy! (10 min)
# Type: yes
```

---

## ✅ ACCESS

```bash
# Get URLs
terraform output

# Dashboard: http://<master-ip>:30800
# Sample App: http://<master-ip>:30080/health
# Prometheus: http://<master-ip>:30090
```

---

## 🧪 TEST SELF-HEALING

```powershell
# PowerShell (Windows)
.\load-test.ps1 -MasterIP "<master-ip>" -TestType both
```

```bash
# Bash (Linux/Mac)
chmod +x load-test.sh
./load-test.sh <master-ip> both
```

---

## 🔍 VALIDATE

```bash
# SSH to master
ssh -i ~/.ssh/ai-healing-key ubuntu@<master-ip>

# Run validation
cd /home/ubuntu/ai-platform
bash scripts/validate-deployment.sh

# Watch pods scale
sudo k3s kubectl get pods -n monitoring-demo -w

# Watch HPA
sudo k3s kubectl get hpa -n monitoring-demo -w

# Check logs
sudo k3s kubectl logs -l app=ai-platform -n monitoring-demo --tail=50
```

---

## 📊 COLLECT METRICS (For Report)

```bash
# SSH to master
ssh -i ~/.ssh/ai-healing-key ubuntu@<master-ip>

# Collect metrics
bash /home/ubuntu/ai-platform/scripts/collect-metrics.sh

# Download report
# From local machine:
scp -i ~/.ssh/ai-healing-key ubuntu@<master-ip>:/tmp/mtech-metrics-report-*.txt .
```

---

## 🛠️ USEFUL COMMANDS

```bash
# Check cluster
sudo k3s kubectl get nodes
sudo k3s kubectl get pods -A
sudo k3s kubectl top nodes

# Check monitoring namespace
sudo k3s kubectl get all -n monitoring-demo
sudo k3s kubectl get hpa -n monitoring-demo

# Check API status
curl http://localhost:30800/api/v1/status | jq .

# Check anomalies
curl http://localhost:30800/api/v1/anomalies | jq .

# Check healing actions
curl http://localhost:30800/api/v1/healing-actions | jq .

# Scale manually (for testing)
sudo k3s kubectl scale deployment sample-app -n monitoring-demo --replicas=6

# Restart deployment
sudo k3s kubectl rollout restart deployment/ai-platform -n monitoring-demo

# View logs
sudo k3s kubectl logs -l app=ai-platform -n monitoring-demo -f
```

---

## 🔧 TROUBLESHOOTING

```bash
# Dashboard not loading?
sudo k3s kubectl get pods -n monitoring-demo
sudo k3s kubectl logs -l app=ai-platform -n monitoring-demo

# HPA shows <unknown>?
sleep 90  # Wait for metrics to populate
sudo k3s kubectl get hpa -n monitoring-demo

# Pods not scaling?
sudo k3s kubectl describe hpa sample-app -n monitoring-demo

# Worker not joined?
sudo k3s kubectl get nodes
ssh -i ~/.ssh/ai-healing-key ubuntu@<worker-ip>
sudo systemctl status k3s-agent
```

---

## 💰 COST MANAGEMENT

```bash
# Stop instances (from local machine)
aws ec2 stop-instances --instance-ids <master-id> <worker-id>

# Start instances
aws ec2 start-instances --instance-ids <master-id> <worker-id>

# Get instance IDs
terraform output
```

---

## 🧹 CLEANUP

```bash
# Destroy everything
terraform destroy
# Type: yes

# Verify in AWS Console
# EC2 → Instances (should be terminated)
```

---

## 📁 FILE STRUCTURE

```
ai-platform-terraform/
├── main.tf                      # Infrastructure definition
├── variables.tf                 # Configuration parameters
├── outputs.tf                   # Access information
├── terraform.tfvars.example     # Config template
├── load-test.ps1               # Load testing script
├── README.md                   # Full documentation
├── QUICK_START.md              # 15-min guide
├── TROUBLESHOOTING.md          # Issue fixes
├── ARCHITECTURE.md             # Diagrams
└── scripts/
    ├── master-init.sh           # Master setup
    ├── worker-init.sh           # Worker setup
    ├── deploy-all.sh            # App deployment
    ├── validate-deployment.sh   # Validation
    └── collect-metrics.sh       # Metrics collection
```

---

## 🎯 SUCCESS CRITERIA

✅ terraform apply completes without errors
✅ Dashboard loads at http://<master-ip>:30800
✅ Health Score = 100%
✅ Both nodes show "Ready"
✅ 4+ pods running (distributed across nodes)
✅ HPA shows cpu: X%/60%
✅ Load test triggers scaling
✅ Anomalies auto-detected
✅ Self-healing actions logged

---

## ⏱️ TIMELINE

- Setup: 5 minutes
- Deploy: 10 minutes
- Validate: 2 minutes
- Test: 3 minutes
**Total: 20 minutes from zero to working demo!**

---

## 🆘 QUICK HELP

**Issue**: Can't SSH
**Fix**: Check security group allows port 22 from your IP

**Issue**: Dashboard timeout
**Fix**: Wait 2-3 minutes after deployment, then check pods

**Issue**: HPA <unknown>
**Fix**: Wait 90 seconds for metrics to populate

**Issue**: Self-healing not working
**Fix**: Run more aggressive load test, check HPA describe

**Issue**: Everything broken
**Fix**: `terraform destroy` then `terraform apply` (15 min)

---

## 📞 DOCUMENTATION

- **Full Guide**: README.md
- **Quick Start**: QUICK_START.md
- **Troubleshooting**: TROUBLESHOOTING.md
- **Architecture**: ARCHITECTURE.md
- **Checklist**: DEPLOYMENT_CHECKLIST.md

---

## 🎓 FOR PRESENTATION

**Demo Flow** (10 minutes):
1. Show terraform output (1 min)
2. Open dashboard (2 min)
3. SSH show cluster (2 min)
4. Run load test (2 min)
5. Show self-healing (3 min)

**Key Points**:
- Fully automated (Infrastructure as Code)
- Production-grade (multi-node, auto-scaling)
- AI/ML powered (anomaly detection)
- Cost-effective (~$15/month)
- Zero manual intervention

---

**Good luck with your MTech demonstration! 🎓🚀**

Project: AI/ML-Driven Self-Healing Platform
Student: Piyush Raval
Institution: IIT Patna
Version: v17 (Terraform Automated)
