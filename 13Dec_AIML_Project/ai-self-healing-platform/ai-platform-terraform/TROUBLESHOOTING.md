# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: Terraform Apply Fails

#### Error: "InvalidKeyPair.NotFound"
```
Error: Error launching source instance: InvalidKeyPair.NotFound
```

**Cause**: SSH key not found or incorrect path

**Solution**:
```bash
# Verify key exists
ls -la ~/.ssh/ai-healing-key*

# Should show both:
# ~/.ssh/ai-healing-key (private)
# ~/.ssh/ai-healing-key.pub (public)

# If missing, generate:
ssh-keygen -t rsa -b 4096 -f ~/.ssh/ai-healing-key

# Update terraform.tfvars with correct paths
```

---

#### Error: "UnauthorizedOperation"
```
Error: UnauthorizedOperation: You are not authorized to perform this operation
```

**Cause**: AWS credentials invalid or insufficient permissions

**Solution**:
```bash
# Verify credentials
aws sts get-caller-identity

# Should return your account ID
# If error, reconfigure:
aws configure

# Or export environment variables:
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

---

#### Error: "InvalidAMIID.NotFound"
```
Error: InvalidAMIID.NotFound: The image id '[ami-xxxxx]' does not exist
```

**Cause**: AMI ID is region-specific

**Solution**:
```bash
# Find correct Ubuntu 22.04 AMI for your region
aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text

# Update terraform.tfvars:
ami_id = "ami-xxxxxxxxx"  # Use the AMI from above command
```

---

### Issue 2: Dashboard Not Accessible

#### Symptom: Browser shows "Connection refused" or timeout

**Diagnosis**:
```bash
# SSH to master
ssh -i ~/.ssh/ai-healing-key ubuntu@<master-ip>

# Check if pods are running
sudo k3s kubectl get pods -n monitoring-demo

# Expected output:
# NAME                           READY   STATUS    RESTARTS   AGE
# ai-platform-xxxxx-xxxxx        1/1     Running   0          5m
# sample-app-xxxxx-xxxxx         1/1     Running   0          5m
```

**Solutions**:

**A) Pods not running:**
```bash
# Check pod status
sudo k3s kubectl describe pod -n monitoring-demo -l app=ai-platform

# Check logs
sudo k3s kubectl logs -n monitoring-demo -l app=ai-platform --tail=50

# Common fix: Restart deployment
sudo k3s kubectl rollout restart deployment/ai-platform -n monitoring-demo
```

**B) Service not created:**
```bash
# Check services
sudo k3s kubectl get svc -n monitoring-demo

# Should show:
# NAME          TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)
# ai-platform   NodePort   10.43.xxx.xxx   <none>        80:30800/TCP

# If missing, reapply:
cd /home/ubuntu/ai-platform
sudo k3s kubectl apply -f kubernetes/ai-platform.yaml
```

**C) Security group issue:**
```bash
# From local machine, test master IP
curl http://<master-ip>:30800/api/v1/status

# If timeout, check AWS Console:
# EC2 → Security Groups → ai-healing-platform-sg
# Verify inbound rules include:
# - Port 30800 from 0.0.0.0/0
```

---

### Issue 3: HPA Shows `<unknown>`

#### Symptom: `kubectl get hpa` shows CPU as `<unknown>`

**Diagnosis**:
```bash
# Check metrics-server
sudo k3s kubectl get pods -n kube-system | grep metrics-server

# Check if metrics are available
sudo k3s kubectl top nodes
sudo k3s kubectl top pods -n monitoring-demo
```

**Solutions**:

**A) Metrics-server not running:**
```bash
# Reinstall metrics-server
sudo k3s kubectl delete deployment metrics-server -n kube-system

# Reinstall
sudo k3s kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch for insecure TLS
sudo k3s kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

# Wait 60 seconds
sleep 60

# Verify
sudo k3s kubectl top nodes
```

**B) Pods missing resource requests:**
```bash
# Check if sample-app has resources defined
sudo k3s kubectl get deployment sample-app -n monitoring-demo -o jsonpath='{.spec.template.spec.containers[0].resources}'

# Should show:
# {"limits":{"cpu":"500m","memory":"256Mi"},"requests":{"cpu":"100m","memory":"128Mi"}}

# If empty, redeploy:
cd /home/ubuntu/ai-platform
sudo k3s kubectl apply -f kubernetes/sample-app.yaml
```

**C) Wait for initialization:**
```bash
# HPA needs 60-90 seconds to start showing CPU
sleep 90
sudo k3s kubectl get hpa -n monitoring-demo

# Should now show: cpu: X%/60%
```

---

### Issue 4: Worker Not Joining Cluster

#### Symptom: `kubectl get nodes` shows only master

**Diagnosis**:
```bash
# Check nodes
sudo k3s kubectl get nodes

# Should show both master and worker
# If only master:

# SSH to worker
ssh -i ~/.ssh/ai-healing-key ubuntu@<worker-ip>

# Check k3s agent status
sudo systemctl status k3s-agent

# Check logs
sudo journalctl -u k3s-agent -n 50
```

**Solutions**:

**A) k3s agent not running:**
```bash
# On worker, restart agent
sudo systemctl restart k3s-agent

# Check status
sudo systemctl status k3s-agent
```

**B) Network connectivity issue:**
```bash
# From worker, test master connectivity
nc -zv <master-private-ip> 6443

# Should show: succeeded!

# If fails, check security group allows internal traffic
```

**C) Token mismatch:**
```bash
# On worker, check token
sudo cat /etc/systemd/system/k3s-agent.service.env | grep K3S_TOKEN

# Should match master token (from terraform.tfvars)

# If mismatch, reinstall k3s on worker:
curl -sfL https://get.k3s.io | K3S_URL=https://<master-private-ip>:6443 \
  K3S_TOKEN=<correct-token> \
  INSTALL_K3S_EXEC="agent --node-name=worker" sh -
```

---

### Issue 5: Pods Not Distributed Across Nodes

#### Symptom: All pods running on master, worker idle

**Diagnosis**:
```bash
# Check pod distribution
sudo k3s kubectl get pods -n monitoring-demo -o wide

# Check for nodeSelector
sudo k3s kubectl get deployment sample-app -n monitoring-demo -o yaml | grep -A 5 nodeSelector
```

**Solution**:
```bash
# Remove nodeSelector to allow worker scheduling
sudo k3s kubectl patch deployment sample-app -n monitoring-demo --type=json \
  -p='[{"op": "remove", "path": "/spec/template/spec/nodeSelector"}]'

# Restart deployment
sudo k3s kubectl rollout restart deployment/sample-app -n monitoring-demo

# Verify distribution
sudo k3s kubectl get pods -n monitoring-demo -o wide
```

---

### Issue 6: Prometheus Not Connected

#### Symptom: Dashboard shows Prometheus: Disconnected (red)

**Diagnosis**:
```bash
# Check Prometheus pod
sudo k3s kubectl get pods -n monitoring

# Check Prometheus service
sudo k3s kubectl get svc -n monitoring

# Test from master
curl http://prometheus-server.monitoring.svc.cluster.local/api/v1/query?query=up
```

**Solutions**:

**A) Prometheus not running:**
```bash
# Check logs
sudo k3s kubectl logs -n monitoring -l app=prometheus-server

# Restart
sudo k3s kubectl rollout restart deployment/prometheus-server -n monitoring
```

**B) Wrong URL in ConfigMap:**
```bash
# Check ConfigMap
sudo k3s kubectl get configmap ai-platform-config -n monitoring-demo -o yaml | grep PROMETHEUS_URL

# Should be: http://prometheus-server.monitoring.svc.cluster.local

# If wrong, update:
sudo k3s kubectl delete configmap ai-platform-config -n monitoring-demo
sudo k3s kubectl create configmap ai-platform-config -n monitoring-demo \
  --from-literal=PROMETHEUS_URL=http://prometheus-server.monitoring.svc.cluster.local \
  --from-literal=PROMETHEUS_ENABLED=true \
  --from-literal=KUBERNETES_ENABLED=true

# Restart AI platform
sudo k3s kubectl rollout restart deployment/ai-platform -n monitoring-demo
```

---

### Issue 7: Self-Healing Not Triggering

#### Symptom: Load test runs but no pods scale

**Diagnosis**:
```bash
# Check HPA
sudo k3s kubectl get hpa -n monitoring-demo

# Check HPA events
sudo k3s kubectl describe hpa sample-app -n monitoring-demo

# Check current CPU usage
sudo k3s kubectl top pods -n monitoring-demo
```

**Solutions**:

**A) CPU not high enough:**
```bash
# CPU must exceed 60% to trigger scaling
# Run more aggressive load test (from local machine):

# PowerShell:
for ($i = 1; $i -le 100; $i++) {
    Start-Job -ScriptBlock {
        Invoke-WebRequest -Uri "http://<master-ip>:30080/compute" -UseBasicParsing
    }
}
```

**B) HPA not configured:**
```bash
# Verify HPA exists
sudo k3s kubectl get hpa -n monitoring-demo

# If missing, create:
sudo k3s kubectl autoscale deployment sample-app -n monitoring-demo \
  --cpu-percent=60 --min=4 --max=10
```

**C) Scaling cooldown period:**
```bash
# HPA has default 3-minute cooldown after scaling
# Wait 3 minutes between tests

# Check events to see scaling history
sudo k3s kubectl get events -n monitoring-demo --sort-by='.lastTimestamp'
```

---

### Issue 8: Terraform Destroy Fails

#### Error: Resources still exist

**Solution**:
```bash
# Force destroy with retries
terraform destroy -auto-approve

# If still fails, manually clean up in AWS Console:
# 1. EC2 → Instances → Terminate both instances
# 2. VPC → Delete ai-healing-platform-vpc
# 3. EC2 → Security Groups → Delete ai-healing-platform-sg
# 4. EC2 → Key Pairs → Delete ai-healing-platform-key

# Then run:
terraform destroy -auto-approve
```

---

## Quick Diagnostics Commands

### Complete Health Check
```bash
#!/bin/bash
echo "=== CLUSTER STATUS ==="
sudo k3s kubectl get nodes

echo -e "\n=== PODS STATUS ==="
sudo k3s kubectl get pods -A

echo -e "\n=== MONITORING-DEMO NAMESPACE ==="
sudo k3s kubectl get all -n monitoring-demo

echo -e "\n=== HPA STATUS ==="
sudo k3s kubectl get hpa -n monitoring-demo

echo -e "\n=== RESOURCE USAGE ==="
sudo k3s kubectl top nodes
sudo k3s kubectl top pods -n monitoring-demo

echo -e "\n=== RECENT EVENTS ==="
sudo k3s kubectl get events -n monitoring-demo --sort-by='.lastTimestamp' | tail -10

echo -e "\n=== API STATUS ==="
curl -s http://localhost:30800/api/v1/status | jq .
```

### Save this as `/home/ubuntu/check-health.sh` and run when troubleshooting

---

## Getting Help

### Collect Diagnostic Information

```bash
# Run this and share output when asking for help
cat > /tmp/diagnostics.sh <<'EOF'
#!/bin/bash
echo "=== TERRAFORM VERSION ==="
terraform version

echo -e "\n=== AWS REGION ==="
aws configure get region

echo -e "\n=== NODES ==="
sudo k3s kubectl get nodes -o wide

echo -e "\n=== PODS ==="
sudo k3s kubectl get pods -A -o wide

echo -e "\n=== SERVICES ==="
sudo k3s kubectl get svc -A

echo -e "\n=== HPA ==="
sudo k3s kubectl get hpa -A

echo -e "\n=== RECENT LOGS - AI Platform ==="
sudo k3s kubectl logs -n monitoring-demo -l app=ai-platform --tail=30

echo -e "\n=== RECENT LOGS - Sample App ==="
sudo k3s kubectl logs -n monitoring-demo -l app=sample-app --tail=20

echo -e "\n=== CONFIGMAP ==="
sudo k3s kubectl get configmap ai-platform-config -n monitoring-demo -o yaml

echo -e "\n=== SECURITY GROUPS ==="
aws ec2 describe-security-groups --filters "Name=group-name,Values=ai-healing-platform-sg" --query 'SecurityGroups[0].IpPermissions'
EOF

chmod +x /tmp/diagnostics.sh
/tmp/diagnostics.sh > /tmp/diagnostics-output.txt 2>&1
cat /tmp/diagnostics-output.txt
```

---

## Prevention Best Practices

1. **Always verify AWS credentials** before `terraform apply`
2. **Use correct SSH key paths** in terraform.tfvars
3. **Wait full deployment time** (10 minutes minimum)
4. **Check outputs** after successful apply
5. **Test dashboard access** before load testing
6. **Wait for HPA initialization** (90 seconds) before expecting scaling
7. **Run gradual load tests** to avoid overwhelming instances
8. **Monitor AWS costs** regularly
9. **Stop instances** when not in use
10. **Keep backups** of terraform.tfstate

---

## Emergency Recovery

### If Everything Breaks:

```bash
# 1. Destroy everything
terraform destroy -auto-approve

# 2. Wait 5 minutes for cleanup

# 3. Verify all resources deleted in AWS Console

# 4. Re-deploy from scratch
terraform init
terraform apply -auto-approve

# 5. Wait 10-12 minutes

# 6. Verify deployment
terraform output
```

**This takes 15-20 minutes but guarantees a clean, working state!**

---

## Contact & Support

- **Check logs first**: `kubectl logs -n monitoring-demo`
- **Review README.md**: Comprehensive documentation
- **Follow QUICK_START.md**: Step-by-step guide
- **Use DEPLOYMENT_CHECKLIST.md**: Validation steps

**Most issues are solved by:**
1. Waiting longer (deployments take time)
2. Restarting pods (`kubectl rollout restart`)
3. Checking AWS Console (verify instances running)
4. Reviewing security groups (verify ports open)
5. Re-deploying (`terraform destroy` + `terraform apply`)
