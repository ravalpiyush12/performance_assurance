# AWS Free Tier Deployment Guide
## AI Self-Healing Platform on AWS

---

## 📋 **QUICK START**

### **Prerequisites**
1. AWS Account (Free tier eligible)
2. AWS CLI installed and configured
3. Terraform installed (v1.0+)
4. SSH key pair created in AWS

---

## 🚀 **OPTION 1: Deploy with Terraform (Recommended)**

### **Step 1: Setup**

```bash
# Clone/download project
cd terraform/

# Create SSH key in AWS
aws ec2 create-key-pair \
  --key-name mtech-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/mtech-key.pem

chmod 400 ~/.ssh/mtech-key.pem

# Configure Terraform variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars:
nano terraform.tfvars
# Set:
#   key_name = "mtech-key"
#   aws_region = "us-east-1"  # or your preferred region
#   allowed_ssh_cidr = "YOUR_IP/32"  # Your public IP
```

### **Step 2: Deploy Infrastructure**

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy (takes ~10 minutes)
terraform apply

# Save outputs
terraform output -json > cluster-info.json
```

### **Step 3: Access Cluster**

```bash
# Get master IP
MASTER_IP=$(terraform output -raw cluster_info | jq -r '.master_public_ip')

# Wait for k3s to initialize (~5 minutes)
sleep 300

# Get kubeconfig
scp -i ~/.ssh/mtech-key.pem \
  ubuntu@$MASTER_IP:/etc/rancher/k3s/k3s.yaml \
  ~/.kube/aws-config

# Update kubeconfig with public IP
sed -i "s/127.0.0.1/$MASTER_IP/g" ~/.kube/aws-config

# Set KUBECONFIG
export KUBECONFIG=~/.kube/aws-config

# Verify cluster
kubectl get nodes
# Should show 2 nodes: master + worker
```

### **Step 4: Deploy AI Platform**

```bash
# SSH to master
ssh -i ~/.ssh/mtech-key.pem ubuntu@$MASTER_IP

# Clone your project
git clone <YOUR_REPO_URL>
cd ai-self-healing-platform

# Build Docker images on master
eval $(minikube docker-env) # Not needed on AWS
docker build -f Dockerfile.sample -t sample-app:latest .
docker build -f Dockerfile.platform -t ai-platform:v17 .

# Deploy
kubectl apply -f kubernetes/

# Verify deployments
kubectl get pods -n monitoring-demo
kubectl get svc -n monitoring-demo
```

### **Step 5: Access Services**

```bash
# Get master IP
MASTER_IP=$(terraform output -raw cluster_info | jq -r '.master_public_ip')

# Dashboard
echo "Dashboard: http://$MASTER_IP:30888"

# Prometheus
echo "Prometheus: http://$MASTER_IP:30090"

# Sample App
echo "Sample App: http://$MASTER_IP:30080"
```

---

## 🧪 **Run Validation**

```bash
# On your local machine (with kubeconfig configured)
python validate_self_healing.py \
  --url http://$MASTER_IP:30080 \
  --ai-platform http://$MASTER_IP:30888 \
  --scenario all

# Advanced experiments
python advanced_experiments.py \
  --url http://$MASTER_IP:30080 \
  --experiment all
```

---

## 🔧 **OPTION 2: Manual Deployment (Without Terraform)**

```bash
# Run the setup script
chmod +x aws-setup.sh
./aws-setup.sh

# Follow the prompts
# Script will create:
# - VPC and subnets
# - Security groups
# - EC2 instances (t3.micro x 2)
# - k3s cluster
# - Prometheus

# After completion, follow steps 3-5 from Terraform option
```

---

## 💰 **Cost Breakdown**

### **Free Tier (First 12 Months)**
- ✅ **EC2**: 750 hours/month t3.micro (2 instances = FREE)
- ✅ **EBS**: 30GB general purpose SSD (FREE)
- ✅ **Data Transfer**: 15GB outbound (FREE)
- ✅ **Load Balancer**: 750 hours/month (FREE)

### **After Free Tier**
- 💵 EC2 t3.micro: ~$7/month per instance
- 💵 EBS 30GB: ~$3/month
- **Total**: ~$17/month (can stop when not in use)

### **Cost Optimization**
```bash
# Stop instances when not using
terraform destroy  # Destroys everything

# Or manually stop
aws ec2 stop-instances --instance-ids <INSTANCE_IDS>

# Start again
aws ec2 start-instances --instance-ids <INSTANCE_IDS>
```

---

## 🐛 **Troubleshooting**

### **Issue: Can't SSH to instances**
```bash
# Check security group allows your IP
aws ec2 describe-security-groups \
  --group-ids <SG_ID> \
  --query 'SecurityGroups[0].IpPermissions'

# Update security group
aws ec2 authorize-security-group-ingress \
  --group-id <SG_ID> \
  --protocol tcp \
  --port 22 \
  --cidr $(curl -s ifconfig.me)/32
```

### **Issue: Worker not joining cluster**
```bash
# SSH to master
ssh -i ~/.ssh/mtech-key.pem ubuntu@<MASTER_IP>

# Check k3s status
sudo systemctl status k3s

# Get token
sudo cat /var/lib/rancher/k3s/server/node-token

# SSH to worker and manually join
ssh -i ~/.ssh/mtech-key.pem ubuntu@<WORKER_IP>

curl -sfL https://get.k3s.io | \
  K3S_URL=https://<MASTER_PRIVATE_IP>:6443 \
  K3S_TOKEN=<TOKEN> \
  sh -s - agent
```

### **Issue: Pods not starting**
```bash
# Check pod status
kubectl describe pod <POD_NAME> -n monitoring-demo

# Check logs
kubectl logs <POD_NAME> -n monitoring-demo

# Check node resources
kubectl top nodes
```

---

## 🧹 **Cleanup**

### **Complete Cleanup (Terraform)**
```bash
terraform destroy
# Type 'yes' to confirm
```

### **Manual Cleanup**
```bash
# Delete instances
aws ec2 terminate-instances --instance-ids <INSTANCE_IDS>

# Delete VPC (after instances are terminated)
aws ec2 delete-vpc --vpc-id <VPC_ID>

# Delete key pair
aws ec2 delete-key-pair --key-name mtech-key
rm ~/.ssh/mtech-key.pem
```

---

## 📊 **Monitoring & Logs**

### **Check cluster status**
```bash
kubectl get nodes
kubectl get pods -A
kubectl top nodes
kubectl top pods -n monitoring-demo
```

### **View logs**
```bash
# AI Platform logs
kubectl logs -f deployment/ai-platform -n monitoring-demo

# Sample app logs
kubectl logs -f deployment/sample-app -n monitoring-demo

# System logs on instances
ssh -i ~/.ssh/mtech-key.pem ubuntu@<INSTANCE_IP>
sudo journalctl -u k3s -f
```

---

## 🎓 **For Demo/Presentation**

1. **Deploy cluster**: `terraform apply` (10 min)
2. **Deploy platform**: `kubectl apply -f kubernetes/` (2 min)
3. **Run validation**: `python validate_self_healing.py` (15 min)
4. **Show dashboard**: Open `http://<MASTER_IP>:30888`
5. **Cleanup**: `terraform destroy` (5 min)

**Total time**: ~35 minutes

---

## 📝 **Next Steps**

- [ ] Deploy to AWS
- [ ] Run validation suite
- [ ] Collect metrics for report
- [ ] Take screenshots
- [ ] Create demo video
- [ ] Document results
