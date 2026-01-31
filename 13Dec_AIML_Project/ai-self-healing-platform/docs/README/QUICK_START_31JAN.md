# AI/ML Self-Healing Platform - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker Desktop installed
- kubectl installed
- AWS CLI configured (for cloud deployment)
- Python 3.11+

---

## 📦 OPTION 1: Local Docker (Fastest - 2 Minutes)

### Step 1: Clone and Setup
```bash
git clone <your-repo>
cd self-healing-platform
```

### Step 2: Run with Docker Compose
```bash
# Start all services (API + Redis + Prometheus + Grafana)
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Step 3: Access Dashboard
- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Stop Services
```bash
docker-compose down
```

---

## ☸️ OPTION 2: Kubernetes Deployment (Production - 10 Minutes)

### Step 1: Prerequisites Check
```bash
# Check kubectl
kubectl version --client

# Check cluster connection
kubectl cluster-info

# Check Docker
docker --version
```

### Step 2: Deploy to Kubernetes
```bash
# Make script executable
chmod +x deploy-to-kubernetes.sh

# Deploy (builds image, creates namespace, deploys)
./deploy-to-kubernetes.sh latest
```

### Step 3: Verify Deployment
```bash
# Check pods
kubectl get pods -n self-healing-platform

# Check services
kubectl get svc -n self-healing-platform

# View logs
kubectl logs -f deployment/self-healing-platform -n self-healing-platform
```

### Step 4: Access Application
```bash
# Get external IP
kubectl get svc self-healing-platform -n self-healing-platform

# Access dashboard at http://<EXTERNAL-IP>
```

### Step 5: Test Auto-Scaling
```bash
# Generate load
kubectl run load-generator --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://self-healing-platform:8000/health; done"

# Watch HPA scale up
kubectl get hpa -n self-healing-platform --watch
```

---

## ☁️ OPTION 3: AWS EKS Deployment (Full Cloud - 15 Minutes)

### Step 1: Create EKS Cluster
```bash
# Install eksctl
brew install eksctl  # macOS
# or download from https://eksctl.io/

# Create cluster
eksctl create cluster \
  --name self-healing-platform \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed
```

### Step 2: Configure kubectl
```bash
aws eks update-kubeconfig --region us-east-1 --name self-healing-platform
```

### Step 3: Create ECR Repository
```bash
# Create repository
aws ecr create-repository --repository-name self-healing-platform --region us-east-1

# Get repository URL
export ECR_REPOSITORY_URL=$(aws ecr describe-repositories \
  --repository-names self-healing-platform \
  --region us-east-1 \
  --query 'repositories[0].repositoryUri' \
  --output text)

echo $ECR_REPOSITORY_URL
```

### Step 4: Deploy Application
```bash
# Deploy to EKS (will push to ECR)
./deploy-to-kubernetes.sh latest

# Wait for load balancer
kubectl get svc self-healing-platform -n self-healing-platform --watch
```

### Step 5: Install Metrics Server (for HPA)
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Step 6: Install Nginx Ingress (Optional - for custom domain)
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/aws/deploy.yaml
```

---

## 🧪 Testing Your Deployment

### Test 1: Health Check
```bash
curl http://<EXTERNAL-IP>/health
# Should return: {"status": "healthy", ...}
```

### Test 2: API Endpoint
```bash
curl http://<EXTERNAL-IP>/api/v1/status
# Should return: {"health_score": 95, ...}
```

### Test 3: Load Test (Trigger Auto-Scaling)
```bash
# Install Apache Bench (if not installed)
sudo apt-get install apache2-utils  # Ubuntu
brew install httpie  # macOS

# Generate load (1000 requests, 10 concurrent)
ab -n 1000 -c 10 http://<EXTERNAL-IP>/api/v1/metrics

# Watch auto-scaling
kubectl get hpa -n self-healing-platform --watch
```

### Test 4: WebSocket Connection
```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://<EXTERNAL-IP>/ws/live
```

---

## 📊 Monitoring

### View Metrics in Prometheus
```bash
# Port forward Prometheus
kubectl port-forward svc/prometheus -n self-healing-platform 9090:9090

# Access at http://localhost:9090
```

### View Dashboards in Grafana
```bash
# Port forward Grafana
kubectl port-forward svc/grafana -n self-healing-platform 3000:3000

# Access at http://localhost:3000
# Login: admin / admin
```

---

## 🐛 Troubleshooting

### Pods Not Starting
```bash
# Check pod status
kubectl get pods -n self-healing-platform

# Describe pod
kubectl describe pod <pod-name> -n self-healing-platform

# Check logs
kubectl logs <pod-name> -n self-healing-platform

# Check events
kubectl get events -n self-healing-platform --sort-by='.lastTimestamp'
```

### Service Not Accessible
```bash
# Check service
kubectl get svc -n self-healing-platform

# Check endpoints
kubectl get endpoints -n self-healing-platform

# Test from within cluster
kubectl run test-pod --image=busybox --rm -it -- \
  wget -O- http://self-healing-platform:8000/health
```

### Image Pull Errors (ECR)
```bash
# Re-authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_REPOSITORY_URL

# Rebuild and push
docker build -t self-healing-platform:latest .
docker tag self-healing-platform:latest $ECR_REPOSITORY_URL:latest
docker push $ECR_REPOSITORY_URL:latest
```

### HPA Not Scaling
```bash
# Check metrics server
kubectl get deployment metrics-server -n kube-system

# Check HPA status
kubectl describe hpa self-healing-platform-hpa -n self-healing-platform

# Check pod metrics
kubectl top pods -n self-healing-platform
```

---

## 🗑️ Cleanup

### Delete Kubernetes Resources
```bash
# Delete namespace (removes everything)
kubectl delete namespace self-healing-platform
```

### Delete EKS Cluster
```bash
eksctl delete cluster --name self-healing-platform --region us-east-1
```

### Stop Docker Compose
```bash
docker-compose down -v
```

---

## 📝 Important Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container image definition |
| `docker-compose.yml` | Local multi-container setup |
| `kubernetes/namespace.yaml` | K8s namespace |
| `kubernetes/deployment.yaml` | K8s deployment + Redis |
| `kubernetes/service.yaml` | K8s services (LoadBalancer) |
| `kubernetes/configmap.yaml` | Configuration + Secrets |
| `kubernetes/hpa.yaml` | Auto-scaling configuration |
| `kubernetes/ingress.yaml` | External access + TLS |
| `deploy-to-kubernetes.sh` | Automated deployment script |

---

## 🎯 Next Steps

1. ✅ **Get it running locally** (Docker Compose)
2. ✅ **Deploy to Kubernetes** (Minikube or EKS)
3. ✅ **Configure monitoring** (Prometheus + Grafana)
4. ✅ **Test auto-scaling** (Load testing)
5. ✅ **Add CI/CD** (GitHub Actions)
6. ✅ **Configure domain** (Ingress + TLS)
7. ✅ **Production hardening** (Security, backups)

---

## 💡 Pro Tips

### Port Forwarding for Local Access
```bash
# Access any service locally
kubectl port-forward svc/self-healing-platform 8000:80 -n self-healing-platform
```

### Quick Logs Access
```bash
# Tail logs
kubectl logs -f deployment/self-healing-platform -n self-healing-platform

# Logs from all pods
kubectl logs -f -l app=self-healing-platform -n self-healing-platform
```

### Manual Scaling
```bash
# Scale to 5 replicas
kubectl scale deployment/self-healing-platform --replicas=5 -n self-healing-platform
```

### Update Deployment (Rolling Update)
```bash
# Update image
kubectl set image deployment/self-healing-platform api=$ECR_REPOSITORY_URL:v2.0 -n self-healing-platform

# Watch rollout
kubectl rollout status deployment/self-healing-platform -n self-healing-platform

# Rollback if needed
kubectl rollout undo deployment/self-healing-platform -n self-healing-platform
```

---

## 🆘 Getting Help

- **Logs**: Check logs first with `kubectl logs`
- **Events**: Check events with `kubectl get events`
- **Describe**: Get detailed info with `kubectl describe`
- **Documentation**: Full docs in `/docs` folder

---

## ✅ Success Checklist

- [ ] Application running locally (Docker Compose)
- [ ] Application deployed to Kubernetes
- [ ] External IP accessible
- [ ] Health check passing
- [ ] Auto-scaling working
- [ ] Monitoring dashboards accessible
- [ ] Load testing successful

---

**You're all set! 🚀**