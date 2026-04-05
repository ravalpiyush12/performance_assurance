# AI Self-Healing Platform - Deployment Checklist

## Pre-Deployment (5 minutes)

- [ ] AWS credentials configured
  ```bash
  aws sts get-caller-identity
  ```

- [ ] Terraform installed
  ```bash
  terraform version
  ```

- [ ] SSH key generated
  ```bash
  ssh-keygen -t rsa -b 4096 -f ~/.ssh/ai-healing-key
  ls -la ~/.ssh/ai-healing-key*
  ```

- [ ] terraform.tfvars configured
  ```bash
  cp terraform.tfvars.example terraform.tfvars
  nano terraform.tfvars
  # Update ssh_public_key_path and ssh_private_key_path
  ```

## Deployment (10 minutes)

- [ ] Initialize Terraform
  ```bash
  terraform init
  ```

- [ ] Review plan
  ```bash
  terraform plan
  ```

- [ ] Apply configuration
  ```bash
  terraform apply
  # Type 'yes' when prompted
  ```

- [ ] Wait for completion (8-12 minutes)
  - Watch output for any errors
  - Note the master IP from outputs

## Post-Deployment Verification (5 minutes)

- [ ] Check Terraform outputs
  ```bash
  terraform output
  ```

- [ ] SSH to master node
  ```bash
  ssh -i ~/.ssh/ai-healing-key ubuntu@<master-ip>
  ```

- [ ] Verify cluster status
  ```bash
  sudo k3s kubectl get nodes
  # Both master and worker should show "Ready"
  
  sudo k3s kubectl get pods -n monitoring-demo -o wide
  # Should see 4-5 pods running
  
  sudo k3s kubectl get hpa -n monitoring-demo
  # Should show cpu: X%/60%
  ```

- [ ] Test dashboard access
  ```
  Open in browser: http://<master-ip>:30800
  ```

- [ ] Verify dashboard shows:
  - [ ] Health Score: 100%
  - [ ] Prometheus: Connected (green)
  - [ ] Kubernetes: Enabled (green)
  - [ ] ML Model: Trained (checkmark)
  - [ ] Total Metrics: 50+
  - [ ] CPU & Memory graphs showing data

- [ ] Test sample app
  ```
  Open in browser: http://<master-ip>:30080/health
  Should return: {"status": "healthy", "service": "sample-app"}
  ```

## Self-Healing Test (5 minutes)

- [ ] Run load test from local machine
  ```powershell
  .\load-test.ps1 -MasterIP "<master-ip>" -TestType both
  ```

- [ ] Watch HPA scaling (on master via SSH)
  ```bash
  sudo k3s kubectl get hpa -n monitoring-demo -w
  # CPU should increase, replicas should scale up
  ```

- [ ] Watch pods scaling
  ```bash
  sudo k3s kubectl get pods -n monitoring-demo -w
  # New pods should appear
  ```

- [ ] Verify dashboard shows:
  - [ ] CPU spike in graph
  - [ ] New anomaly detected (CPU_USAGE)
  - [ ] Self-healing action logged
  - [ ] Error rate graph populated

## Success Criteria

✅ **Deployment Successful If:**
- Both nodes show "Ready"
- 4+ sample-app pods running (distributed across master/worker)
- Dashboard accessible and showing real-time data
- HPA shows actual CPU percentage (not `<unknown>`)
- Load test triggers pod scaling
- Anomalies detected automatically
- Self-healing actions executed

## Troubleshooting

If any checks fail, see README.md troubleshooting section

## Cleanup

- [ ] When done, destroy infrastructure
  ```bash
  terraform destroy
  # Type 'yes' when prompted
  ```

- [ ] Verify in AWS Console
  - EC2 instances terminated
  - VPC deleted
  - Security groups deleted

---

**Estimated Total Time: 25 minutes**
- Pre-deployment: 5 min
- Deployment: 10 min
- Verification: 5 min
- Testing: 5 min

**Cost: ~$0.50/day** (t3.small master + t3.micro worker)
**Free Tier: Worker is free**, Master uses credits (~$15/month from $100 credit)
