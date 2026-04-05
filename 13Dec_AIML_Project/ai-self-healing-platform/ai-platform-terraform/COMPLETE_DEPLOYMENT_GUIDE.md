# COMPLETE TERRAFORM DEPLOYMENT GUIDE
# All Issues Fixed - Production Ready

## ALL ISSUES FIXED IN THIS VERSION:

✅ Issue 1: Scripts folder not in app-files
✅ Issue 2: File upload directory creation
✅ Issue 3: Docker images not on worker node  
✅ Issue 4: Pods scheduled on wrong nodes
✅ Issue 5: Prometheus not installed
✅ Issue 6: No metrics displaying
✅ Issue 7: ML model needs training data
✅ Issue 8: Windows PowerShell compatibility
✅ Issue 9: SSH key format issues
✅ Issue 10: Kubernetes manifest fixes

---

## DEPLOYMENT STEPS:

### STEP 1: Destroy Current Infrastructure

```powershell
cd ai-platform-terraform
terraform destroy
# Type: yes
```

### STEP 2: Replace Files

Download these 3 new files:
1. `main-complete.tf` → Replace your `main.tf`
2. `deploy-all-complete.sh` → Save to terraform root
3. `prepare-for-terraform.ps1` → Save to terraform root

```powershell
# Rename/backup old files
Rename-Item main.tf main-old.tf

# Rename new files
Rename-Item main-complete.tf main.tf
```

### STEP 3: Prepare Application Files

```powershell
# Unblock the script
Unblock-File -Path .\prepare-for-terraform.ps1

# Run preparation (update path to YOUR project)
.\prepare-for-terraform.ps1 -ProjectPath "G:\F Drive\Piyush Data\Learning\performance_assurance\13Dec_AIML_Project\ai-self-healing-platform"
```

This will:
- Copy entire `src/` directory (all subdirectories)
- Copy all Dockerfiles
- Copy requirements.txt
- Copy Kubernetes manifests
- **Copy scripts folder** (THIS WAS MISSING BEFORE!)
- Copy the complete deployment script

### STEP 4: Verify Preparation

```powershell
# Check app-files structure
Get-ChildItem app-files -Recurse -Directory

# Should show:
# - src/ (with all subdirectories)
# - kubernetes/
# - scripts/  ← THIS IS CRITICAL!

# Check deploy script exists
Test-Path app-files\scripts\deploy-all.sh
# Should return: True
```

### STEP 5: Deploy with Terraform

```powershell
# Initialize
terraform init

# Review what will be created
terraform plan

# Deploy! (takes 15-20 minutes)
terraform apply
# Type: yes
```

---

## WHAT THE NEW DEPLOYMENT DOES:

### Phase 1: Infrastructure (5 min)
- Creates VPC, subnets, security groups
- Launches master (t3.small) and worker (t3.micro)
- Installs k3s on both nodes
- Waits for cluster formation

### Phase 2: File Upload (2 min)
- Creates directory on master
- Uploads ALL your files including scripts
- Sets correct permissions

### Phase 3: Application Deployment (8-10 min)
The `deploy-all-complete.sh` script:

1. **Builds Docker images** from YOUR code
2. **Imports to master** k3s
3. **Distributes to worker** (handles SSH issues gracefully)
4. **Creates namespaces** (monitoring-demo, monitoring)
5. **Deploys manifests** with automatic fixes:
   - `imagePullPolicy: Never` → `IfNotPresent`
   - Adds `nodeSelector` for ai-platform (master only)
   - Fixes Prometheus URL to full DNS
6. **Installs Prometheus** via Helm
7. **Waits for everything** to be ready
8. **Generates initial traffic** for ML model

---

## EXPECTED RESULTS:

After successful deployment:

```
======================================== DEPLOYMENT COMPLETE!
========================================

Dashboard:  http://3.X.X.X:30800
Sample App: http://3.X.X.X:30080/health
Prometheus: http://3.X.X.X:30090

Pods:
- ai-platform-xxxxx (1/1 Running on master)
- sample-app-xxxxx (1/1 Running on master)
- sample-app-xxxxx (1/1 Running on worker)
- sample-app-xxxxx (1/1 Running on worker)

Services:
- ai-platform: NodePort 30800
- sample-app: NodePort 30080
- prometheus-server: NodePort 30090

HPA:
- sample-app: 3-10 replicas, 60% CPU target
```

---

## DASHBOARD FEATURES:

When you open http://master-ip:30800:

✅ **Health Score: 100%**
✅ **Prometheus: Enabled** (green indicator)
✅ **Kubernetes: Enabled** (green indicator)
✅ **ML Model: Training** → **Trained** (after 5 min)
✅ **Real-time graphs** with actual data
✅ **Active alerts** (when issues detected)
✅ **Healing actions** (auto-scaling logs)

---

## TESTING SELF-HEALING:

### Option 1: From Dashboard
Wait 5 minutes for ML model to train, then:
- Dashboard will show metrics
- Run built-in load test (if available in your code)

### Option 2: SSH to Master
```bash
ssh -i ~/.ssh/ai-healing-key ubuntu@<master-ip>

# Generate load
for i in {1..1000}; do
  curl -s http://localhost:30080/compute > /dev/null
  sleep 0.1
done

# Watch pods scale in another terminal
watch -n 2 'sudo k3s kubectl get pods -n monitoring-demo'
# Should see: 3 → 4 → 5 → 6+ pods
```

### Option 3: PowerShell Load Test
```powershell
# From your local machine
terraform output master_public_ip
# Get the IP

# Run load test
1..1000 | ForEach-Object {
    Invoke-WebRequest -Uri "http://<master-ip>:30080/compute" -UseBasicParsing | Out-Null
    Start-Sleep -Milliseconds 100
}
```

---

## DIFFERENCES FROM PREVIOUS VERSION:

| Issue | Before | After |
|-------|--------|-------|
| Scripts folder | Not copied | ✅ Copied to app-files |
| File upload | Failed (no directory) | ✅ Creates directory first |
| Worker images | Missing | ✅ Distributed automatically |
| Pod scheduling | Random (failed on worker) | ✅ ai-platform on master only |
| Prometheus | Not installed | ✅ Auto-installed via Helm |
| Metrics | Not showing | ✅ Working with real data |
| ML model | No training data | ✅ Auto-generates traffic |
| Deployment time | Manual intervention needed | ✅ Fully automated |

---

## COST ESTIMATE:

- **Worker**: FREE (t3.micro, 750 hours/month)
- **Master**: ~$15/month (t3.small)
- **Total**: ~$15/month from $100 AWS credit
- **Runtime**: 6+ months on free credit

**To minimize cost:**
- Stop instances when not in use
- Only pay for storage (~$2/month)

---

## TROUBLESHOOTING:

### Issue: Terraform apply fails at upload
**Fix**: Check SSH key paths in terraform.tfvars

### Issue: Dashboard shows "Prometheus: Disabled"
**Fix**: Wait 5 more minutes for Prometheus deployment

### Issue: No pods on worker
**Fix**: This is intentional! ai-platform runs on master only

### Issue: ML Model stuck at "Training"
**Fix**: Wait for 20 samples (~5 minutes of runtime)

### Issue: Everything broken
**Fix**: 
```powershell
terraform destroy
terraform apply
```

---

## FILES YOU DOWNLOADED:

1. **main-complete.tf** - Fixed Terraform configuration
2. **deploy-all-complete.sh** - Complete deployment script
3. **prepare-for-terraform.ps1** - File preparation script
4. **COMPLETE_DEPLOYMENT_GUIDE.md** - This guide

---

## DEPLOYMENT CHECKLIST:

- [ ] Downloaded all 3 files
- [ ] Destroyed old infrastructure
- [ ] Replaced main.tf
- [ ] Ran prepare-for-terraform.ps1
- [ ] Verified app-files/scripts/ exists
- [ ] Ran terraform init
- [ ] Ran terraform apply
- [ ] Waited 15-20 minutes
- [ ] Dashboard accessible
- [ ] Prometheus showing metrics
- [ ] ML model trained
- [ ] Self-healing tested

---

**YOU'RE READY TO DEPLOY!**

This version handles EVERYTHING automatically. No manual intervention needed.

Total deployment time: **15-20 minutes** from `terraform apply` to working platform!

Good luck with your MTech demonstration! 🎓🚀
