# Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          YOUR LOCAL MACHINE                                 │
│                                                                             │
│  1. Run: terraform apply                                                   │
│  2. Wait: 10 minutes                                                       │
│  3. Access: http://<master-ip>:30800                                       │
│  4. Test: .\load-test.ps1 -MasterIP "<ip>"                                │
│                                                                             │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
                                 │ Terraform Creates:
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              AWS CLOUD                                      │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    VPC: 10.0.0.0/16                                 │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────┐    ┌──────────────────────────┐    │   │
│  │  │  Subnet 1: 10.0.0.0/24   │    │  Subnet 2: 10.0.1.0/24   │    │   │
│  │  │                          │    │                          │    │   │
│  │  │  ┌────────────────────┐ │    │  ┌────────────────────┐ │    │   │
│  │  │  │   MASTER NODE      │ │    │  │   WORKER NODE      │ │    │   │
│  │  │  │   (t3.small)       │ │    │  │   (t3.micro)       │ │    │   │
│  │  │  │   2 vCPU, 2GB RAM  │ │    │  │   2 vCPU, 1GB RAM  │ │    │   │
│  │  │  │                    │ │    │  │                    │ │    │   │
│  │  │  │  ┌──────────────┐ │ │    │  │  ┌──────────────┐ │ │    │   │
│  │  │  │  │ k3s Master   │ │ │    │  │  │ k3s Agent    │ │ │    │   │
│  │  │  │  │ (Control)    │◄┼─┼────┼──┼─►│ (Worker)     │ │ │    │   │
│  │  │  │  └──────────────┘ │ │    │  │  └──────────────┘ │ │    │   │
│  │  │  │                    │ │    │  │                    │ │    │   │
│  │  │  │  Pods:             │ │    │  │  Pods:             │ │    │   │
│  │  │  │  ├─ AI Platform    │ │    │  │  ├─ Sample App    │ │    │   │
│  │  │  │  ├─ Prometheus     │ │    │  │  ├─ Sample App    │ │    │   │
│  │  │  │  ├─ Sample App     │ │    │  │  └─ Sample App    │ │    │   │
│  │  │  │  └─ Sample App     │ │    │  │                    │ │    │   │
│  │  │  │                    │ │    │  │  (Scales 4-10)     │ │    │   │
│  │  │  │  Services:         │ │    │  │                    │ │    │   │
│  │  │  │  ├─ :30800 (UI)    │ │    │  │                    │ │    │   │
│  │  │  │  ├─ :30080 (App)   │ │    │  │                    │ │    │   │
│  │  │  │  └─ :30090 (Prom)  │ │    │  │                    │ │    │   │
│  │  │  └────────────────────┘ │    │  └────────────────────┘ │    │   │
│  │  │      Public IP: X.X.X.X │    │      Public IP: Y.Y.Y.Y │    │   │
│  │  └──────────────────────────┘    └──────────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐ │   │
│  │  │              Internet Gateway                                 │ │   │
│  │  └──────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐ │   │
│  │  │              Security Group                                   │ │   │
│  │  │  - SSH: 22                                                   │ │   │
│  │  │  - k3s API: 6443                                             │ │   │
│  │  │  - HTTP: 80, 443                                             │ │   │
│  │  │  - NodePort: 30000-32767                                     │ │   │
│  │  └──────────────────────────────────────────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  │ You Access Via:
                                  ▼
                    ┌─────────────────────────────┐
                    │   Browser on Port 30800     │
                    │   (Dashboard)               │
                    └─────────────────────────────┘
                    ┌─────────────────────────────┐
                    │   Browser on Port 30080     │
                    │   (Sample App)              │
                    └─────────────────────────────┘
                    ┌─────────────────────────────┐
                    │   SSH to Master             │
                    │   (kubectl commands)        │
                    └─────────────────────────────┘
```

## Deployment Flow

```
START
  │
  ├─► terraform init (1 min)
  │
  ├─► terraform apply (10 min)
  │     │
  │     ├─► Create VPC & Networking (2 min)
  │     │     ├─ VPC
  │     │     ├─ Subnets (2x)
  │     │     ├─ Internet Gateway
  │     │     ├─ Route Tables
  │     │     └─ Security Group
  │     │
  │     ├─► Launch EC2 Instances (2 min)
  │     │     ├─ Master (t3.small)
  │     │     └─ Worker (t3.micro)
  │     │
  │     ├─► Master Init Script (3 min)
  │     │     ├─ Install k3s server
  │     │     ├─ Install metrics-server
  │     │     ├─ Deploy Prometheus
  │     │     └─ Create namespaces
  │     │
  │     ├─► Worker Init Script (1 min)
  │     │     └─ Install k3s agent
  │     │
  │     └─► Deploy Applications (2 min)
  │           ├─ Build Docker images
  │           ├─ Import to k3s
  │           ├─ Apply RBAC
  │           ├─ Apply ConfigMap
  │           ├─ Deploy sample-app (4 pods)
  │           ├─ Deploy ai-platform (1 pod)
  │           └─ Create HPA
  │
  ├─► Outputs Displayed
  │     ├─ Master IP
  │     ├─ Worker IP
  │     ├─ Dashboard URL
  │     └─ SSH Commands
  │
  └─► READY FOR DEMO! ✅
        │
        ├─► Open Dashboard (instant)
        ├─► Run Load Test (2 min)
        └─► Watch Self-Healing (3 min)
```

## Self-Healing Flow

```
Normal State
  │
  ├─► Prometheus scrapes metrics (every 15s)
  ├─► ML model analyzes data
  ├─► Health Score: 100%
  └─► HPA: 4 pods, CPU ~10%
        │
        │  Load Test Triggered
        ▼
High CPU Load
  │
  ├─► CPU usage: 10% → 80%
  ├─► Prometheus detects spike
  └─► AI Platform analyzes
        │
        │  Anomaly Detection
        ▼
CPU_USAGE Anomaly
  │
  ├─► Anomaly Type: CPU_USAGE
  ├─► Severity: CRITICAL
  ├─► Score: -1.5 (threshold: -1.0)
  └─► Logged in dashboard
        │
        │  HPA Decision
        ▼
Auto-Scaling Triggered
  │
  ├─► HPA calculates: CPU 80% > target 60%
  ├─► Desired replicas: 6 (current: 4)
  └─► Kubernetes creates 2 new pods
        │
        │  Pod Creation
        ▼
Pods Distributed
  │
  ├─► Master: 3 pods (+1 new)
  ├─► Worker: 3 pods (+1 new)
  └─► Load balanced across nodes
        │
        │  Self-Healing Complete
        ▼
Recovered State
  │
  ├─► CPU usage: 80% → 30%
  ├─► 6 pods handling load
  ├─► Health Score: 95%
  └─► Healing action logged
        │
        │  Cool Down (5 min)
        ▼
Scale Down
  │
  ├─► Load decreases
  ├─► HPA: CPU < 40%
  ├─► Scale down: 6 → 4 pods
  └─► Return to normal state
```

## Component Interaction

```
┌─────────────┐      scrapes       ┌─────────────┐
│ Prometheus  │◄───────────────────│ Sample App  │
│             │    :5000/metrics   │   Pods      │
└──────┬──────┘                    └─────────────┘
       │
       │ queries
       ▼
┌─────────────┐      analyzes      ┌─────────────┐
│ AI Platform │───────────────────►│ ML Model    │
│             │                     │ (Isolation  │
│             │◄───────────────────│  Forest)    │
└──────┬──────┘   anomaly scores   └─────────────┘
       │
       │ detects anomaly
       ▼
┌─────────────┐                    ┌─────────────┐
│  Dashboard  │                    │     HPA     │
│   (React)   │                    │ (k8s native)│
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │ displays                         │ scales
       ▼                                  ▼
┌─────────────┐      controls      ┌─────────────┐
│    User     │◄───────────────────│ Kubernetes  │
│  (Browser)  │    monitors via    │   Cluster   │
└─────────────┘    kubectl/SSH     └─────────────┘
```
