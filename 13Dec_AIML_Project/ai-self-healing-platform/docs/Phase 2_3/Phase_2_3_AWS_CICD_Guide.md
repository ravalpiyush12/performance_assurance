# PHASE 2 & 3 IMPLEMENTATION - PART 2
## AWS Cloud Integration + CI/CD + Monitoring

---

## 4. AWS CLOUD INTEGRATION

### 4.1 AWS Prerequisites

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region: us-east-1
# Default output format: json

# Install eksctl (EKS management tool)
curl --silent --location "https://github.com/weksctl-io/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Verify installations
aws --version
eksctl version
kubectl version --client
```

### 4.2 EKS Cluster Setup

**File: `aws/eks-cluster-config.yaml`**

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: self-healing-platform-cluster
  region: us-east-1
  version: "1.28"

# IAM OIDC provider for service accounts
iam:
  withOIDC: true

# VPC Configuration
vpc:
  cidr: 10.0.0.0/16
  nat:
    gateway: Single  # Single NAT gateway for cost optimization

# Managed Node Groups
managedNodeGroups:
  - name: platform-nodes
    instanceType: t3.medium
    desiredCapacity: 2
    minSize: 1
    maxSize: 5
    volumeSize: 30
    volumeType: gp3
    
    # Enable IAM role for service accounts
    iam:
      withAddonPolicies:
        autoScaler: true
        cloudWatch: true
        albIngress: true
    
    labels:
      role: platform
      environment: production
    
    tags:
      Project: self-healing-platform
      ManagedBy: eksctl
    
    # Use Spot instances for cost savings (optional)
    spot: false

# CloudWatch Logging
cloudWatch:
  clusterLogging:
    enableTypes: ["api", "audit", "authenticator", "controllerManager", "scheduler"]
```

**File: `scripts/setup_aws_eks.sh`**

```bash
#!/bin/bash

set -e

echo "☁️  Setting up AWS EKS Cluster for Self-Healing Platform"
echo "========================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

CLUSTER_NAME="self-healing-platform-cluster"
REGION="us-east-1"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! command -v eksctl &> /dev/null; then
    echo -e "${RED}❌ eksctl not found. Please install it first.${NC}"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"

# Create EKS cluster
echo -e "${YELLOW}Step 1: Creating EKS cluster (this may take 15-20 minutes)...${NC}"
eksctl create cluster -f aws/eks-cluster-config.yaml

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ EKS cluster created successfully${NC}"
else
    echo -e "${RED}❌ EKS cluster creation failed${NC}"
    exit 1
fi

# Update kubeconfig
echo -e "${YELLOW}Step 2: Updating kubeconfig...${NC}"
aws eks update-kubeconfig --region ${REGION} --name ${CLUSTER_NAME}

# Verify cluster
echo -e "${YELLOW}Step 3: Verifying cluster...${NC}"
kubectl get nodes

# Install AWS Load Balancer Controller
echo -e "${YELLOW}Step 4: Installing AWS Load Balancer Controller...${NC}"

# Create IAM policy
curl -o aws/iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://aws/iam-policy.json

# Create service account
eksctl create iamserviceaccount \
    --cluster=${CLUSTER_NAME} \
    --namespace=kube-system \
    --name=aws-load-balancer-controller \
    --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy \
    --approve

# Install controller using Helm
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    -n kube-system \
    --set clusterName=${CLUSTER_NAME} \
    --set serviceAccount.create=false \
    --set serviceAccount.name=aws-load-balancer-controller

# Install Metrics Server
echo -e "${YELLOW}Step 5: Installing Metrics Server...${NC}"
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Install Cluster Autoscaler
echo -e "${YELLOW}Step 6: Installing Cluster Autoscaler...${NC}"
kubectl apply -f aws/cluster-autoscaler.yaml

echo -e "${GREEN}✅ AWS EKS setup complete!${NC}"
echo ""
echo "📊 Cluster Information:"
kubectl cluster-info

echo ""
echo "📝 Next steps:"
echo "  1. Deploy application: ./scripts/deploy_to_eks.sh"
echo "  2. View dashboard: kubectl proxy &"
echo "  3. Clean up: eksctl delete cluster --name ${CLUSTER_NAME}"
```

### 4.3 AWS-Specific Kubernetes Manifests

**File: `aws/ingress.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: self-healing-platform-ingress
  namespace: self-healing-platform
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '30'
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: '5'
    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    alb.ingress.kubernetes.io/unhealthy-threshold-count: '3'
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: self-healing-platform-service
            port:
              number: 80
```

**File: `aws/cluster-autoscaler.yaml`**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    k8s-addon: cluster-autoscaler.addons.k8s.io
    k8s-app: cluster-autoscaler
  name: cluster-autoscaler
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-autoscaler
  labels:
    k8s-addon: cluster-autoscaler.addons.k8s.io
    k8s-app: cluster-autoscaler
rules:
  - apiGroups: [""]
    resources: ["events", "endpoints"]
    verbs: ["create", "patch"]
  - apiGroups: [""]
    resources: ["pods/eviction"]
    verbs: ["create"]
  - apiGroups: [""]
    resources: ["pods/status"]
    verbs: ["update"]
  - apiGroups: [""]
    resources: ["endpoints"]
    resourceNames: ["cluster-autoscaler"]
    verbs: ["get", "update"]
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["watch", "list", "get", "update"]
  - apiGroups: [""]
    resources:
      - "namespaces"
      - "pods"
      - "services"
      - "replicationcontrollers"
      - "persistentvolumeclaims"
      - "persistentvolumes"
    verbs: ["watch", "list", "get"]
  - apiGroups: ["extensions"]
    resources: ["replicasets", "daemonsets"]
    verbs: ["watch", "list", "get"]
  - apiGroups: ["policy"]
    resources: ["poddisruptionbudgets"]
    verbs: ["watch", "list"]
  - apiGroups: ["apps"]
    resources: ["statefulsets", "replicasets", "daemonsets"]
    verbs: ["watch", "list", "get"]
  - apiGroups: ["storage.k8s.io"]
    resources: ["storageclasses", "csinodes", "csidrivers", "csistoragecapacities"]
    verbs: ["watch", "list", "get"]
  - apiGroups: ["batch", "extensions"]
    resources: ["jobs"]
    verbs: ["get", "list", "watch", "patch"]
  - apiGroups: ["coordination.k8s.io"]
    resources: ["leases"]
    verbs: ["create"]
  - apiGroups: ["coordination.k8s.io"]
    resourceNames: ["cluster-autoscaler"]
    resources: ["leases"]
    verbs: ["get", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  labels:
    k8s-addon: cluster-autoscaler.addons.k8s.io
    k8s-app: cluster-autoscaler
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["create","list","watch"]
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["cluster-autoscaler-status", "cluster-autoscaler-priority-expander"]
    verbs: ["delete", "get", "update", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-autoscaler
  labels:
    k8s-addon: cluster-autoscaler.addons.k8s.io
    k8s-app: cluster-autoscaler
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-autoscaler
subjects:
  - kind: ServiceAccount
    name: cluster-autoscaler
    namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  labels:
    k8s-addon: cluster-autoscaler.addons.k8s.io
    k8s-app: cluster-autoscaler
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: cluster-autoscaler
subjects:
  - kind: ServiceAccount
    name: cluster-autoscaler
    namespace: kube-system
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  labels:
    app: cluster-autoscaler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      priorityClassName: system-cluster-critical
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
        fsGroup: 65534
      serviceAccountName: cluster-autoscaler
      containers:
        - image: registry.k8s.io/autoscaling/cluster-autoscaler:v1.28.2
          name: cluster-autoscaler
          resources:
            limits:
              cpu: 100m
              memory: 600Mi
            requests:
              cpu: 100m
              memory: 600Mi
          command:
            - ./cluster-autoscaler
            - --v=4
            - --stderrthreshold=info
            - --cloud-provider=aws
            - --skip-nodes-with-local-storage=false
            - --expander=least-waste
            - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/self-healing-platform-cluster
            - --balance-similar-node-groups
            - --skip-nodes-with-system-pods=false
          volumeMounts:
            - name: ssl-certs
              mountPath: /etc/ssl/certs/ca-certificates.crt
              readOnly: true
          imagePullPolicy: "Always"
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
                - ALL
            readOnlyRootFilesystem: true
      volumes:
        - name: ssl-certs
          hostPath:
            path: "/etc/ssl/certs/ca-bundle.crt"
```

### 4.4 AWS Integration in Python Code

**File: `src/cloud/aws_integration.py`**

```python
"""
AWS Cloud Integration Module
Provides AWS-specific functionality for self-healing
"""

import boto3
import logging
from typing import Dict, Optional
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSIntegration:
    """
    AWS integration for cloud-native self-healing
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.autoscaling = boto3.client('autoscaling', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.ecs = boto3.client('ecs', region_name=region)
        self.eks = boto3.client('eks', region_name=region)
        
        logger.info(f"✅ AWS Integration initialized (region: {region})")
    
    def scale_autoscaling_group(self, asg_name: str, desired_capacity: int) -> Dict:
        """
        Scale an Auto Scaling Group
        
        Args:
            asg_name: Name of the Auto Scaling Group
            desired_capacity: Desired number of instances
        """
        try:
            logger.info(f"📈 Scaling ASG '{asg_name}' to {desired_capacity} instances")
            
            response = self.autoscaling.set_desired_capacity(
                AutoScalingGroupName=asg_name,
                DesiredCapacity=desired_capacity,
                HonorCooldown=True
            )
            
            logger.info(f"✅ Successfully scaled ASG '{asg_name}'")
            return {'success': True, 'asg_name': asg_name, 'desired_capacity': desired_capacity}
            
        except ClientError as e:
            logger.error(f"❌ Error scaling ASG: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_autoscaling_group_status(self, asg_name: str) -> Optional[Dict]:
        """
        Get Auto Scaling Group status
        """
        try:
            response = self.autoscaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name]
            )
            
            if not response['AutoScalingGroups']:
                return None
            
            asg = response['AutoScalingGroups'][0]
            
            return {
                'name': asg['AutoScalingGroupName'],
                'desired_capacity': asg['DesiredCapacity'],
                'min_size': asg['MinSize'],
                'max_size': asg['MaxSize'],
                'current_instances': len(asg['Instances']),
                'healthy_instances': len([i for i in asg['Instances'] if i['HealthStatus'] == 'Healthy']),
                'availability_zones': asg['AvailabilityZones']
            }
            
        except ClientError as e:
            logger.error(f"❌ Error getting ASG status: {e}")
            return None
    
    def create_cloudwatch_alarm(self, alarm_name: str, metric_name: str, 
                               threshold: float, asg_name: str) -> Dict:
        """
        Create CloudWatch alarm for auto-scaling
        """
        try:
            response = self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=2,
                MetricName=metric_name,
                Namespace='AWS/EC2',
                Period=60,
                Statistic='Average',
                Threshold=threshold,
                ActionsEnabled=True,
                AlarmDescription=f'Alarm for {metric_name} on {asg_name}',
                Dimensions=[
                    {
                        'Name': 'AutoScalingGroupName',
                        'Value': asg_name
                    }
                ]
            )
            
            logger.info(f"✅ Created CloudWatch alarm: {alarm_name}")
            return {'success': True, 'alarm_name': alarm_name}
            
        except ClientError as e:
            logger.error(f"❌ Error creating alarm: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_cloudwatch_metrics(self, namespace: str, metric_name: str, 
                              dimensions: list, minutes: int = 5) -> list:
        """
        Get CloudWatch metrics
        """
        from datetime import datetime, timedelta
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=minutes)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Average', 'Maximum', 'Minimum']
            )
            
            return response.get('Datapoints', [])
            
        except ClientError as e:
            logger.error(f"❌ Error getting metrics: {e}")
            return []
    
    def scale_ecs_service(self, cluster: str, service: str, desired_count: int) -> Dict:
        """
        Scale ECS service
        """
        try:
            logger.info(f"📈 Scaling ECS service '{service}' to {desired_count} tasks")
            
            response = self.ecs.update_service(
                cluster=cluster,
                service=service,
                desiredCount=desired_count
            )
            
            logger.info(f"✅ Successfully scaled ECS service '{service}'")
            return {'success': True, 'service': service, 'desired_count': desired_count}
            
        except ClientError as e:
            logger.error(f"❌ Error scaling ECS service: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_eks_nodegroup_scaling(self, cluster_name: str, nodegroup_name: str,
                                    min_size: int, max_size: int, desired_size: int) -> Dict:
        """
        Update EKS node group scaling configuration
        """
        try:
            logger.info(f"📈 Updating EKS nodegroup '{nodegroup_name}' scaling")
            
            response = self.eks.update_nodegroup_config(
                clusterName=cluster_name,
                nodegroupName=nodegroup_name,
                scalingConfig={
                    'minSize': min_size,
                    'maxSize': max_size,
                    'desiredSize': desired_size
                }
            )
            
            logger.info(f"✅ Successfully updated EKS nodegroup scaling")
            return {
                'success': True,
                'cluster': cluster_name,
                'nodegroup': nodegroup_name,
                'scaling': {
                    'min': min_size,
                    'max': max_size,
                    'desired': desired_size
                }
            }
            
        except ClientError as e:
            logger.error(f"❌ Error updating EKS nodegroup: {e}")
            return {'success': False, 'error': str(e)}


# Example usage
if __name__ == '__main__':
    aws = AWSIntegration(region='us-east-1')
    
    # Get ASG status
    status = aws.get_autoscaling_group_status('my-asg')
    if status:
        print(f"ASG Status: {status}")
    
    # Scale ASG
    result = aws.scale_autoscaling_group('my-asg', desired_capacity=5)
    print(f"Scale Result: {result}")
    
    # Create CloudWatch alarm
    alarm = aws.create_cloudwatch_alarm(
        alarm_name='high-cpu-alarm',
        metric_name='CPUUtilization',
        threshold=80.0,
        asg_name='my-asg'
    )
    print(f"Alarm Created: {alarm}")
```

---

## 6. CI/CD PIPELINE (GITHUB ACTIONS)

### 6.1 GitHub Actions Workflows

Create directory:
```bash
mkdir -p .github/workflows
```

**File: `.github/workflows/ci.yml`**

```yaml
name: CI - Build and Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'

jobs:
  # Job 1: Python Linting and Testing
  python-tests:
    name: Python Tests
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio black flake8 mypy
    
    - name: Run Black (code formatting)
      run: black --check src/
    
    - name: Run Flake8 (linting)
      run: flake8 src/ --max-line-length=120
    
    - name: Run MyPy (type checking)
      run: mypy src/ --ignore-missing-imports
    
    - name: Run unit tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Archive coverage results
      uses: actions/upload-artifact@v4
      with:
        name: coverage-report
        path: htmlcov/
  
  # Job 2: Docker Build
  docker-build:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: python-tests
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Build Docker image
      run: |
        docker build -t self-healing-platform:${{ github.sha }} .
    
    - name: Save Docker image
      run: |
        docker save self-healing-platform:${{ github.sha }} > image.tar
    
    - name: Upload Docker image artifact
      uses: actions/upload-artifact@v4
      with:
        name: docker-image
        path: image.tar
        retention-days: 1
  
  # Job 3: Integration Tests
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: docker-build
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Download Docker image
      uses: actions/download-artifact@v4
      with:
        name: docker-image
    
    - name: Load Docker image
      run: docker load < image.tar
    
    - name: Start platform
      run: |
        docker run -d -p 8000:8000 --name platform self-healing-platform:${{ github.sha }}
        sleep 10
    
    - name: Run health check
      run: |
        curl -f http://localhost:8000/health || exit 1
    
    - name: Run integration tests
      run: |
        pip install requests pytest
        pytest tests/integration/ -v
    
    - name: Stop platform
      if: always()
      run: docker stop platform
  
  # Job 4: Security Scan
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: docker-build
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Run Bandit (Python security)
      run: |
        pip install bandit
        bandit -r src/ -f json -o bandit-report.json
    
    - name: Run Safety (dependencies check)
      run: |
        pip install safety
        safety check --json > safety-report.json
    
    - name: Download Docker image
      uses: actions/download-artifact@v4
      with:
        name: docker-image
    
    - name: Load Docker image
      run: docker load < image.tar
    
    - name: Run Trivy (container scan)
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: self-healing-platform:${{ github.sha }}
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v3
      with:
        sarif_file: 'trivy-results.sarif'
```

**File: `.github/workflows/cd-staging.yml`**

```yaml
name: CD - Deploy to Staging

on:
  push:
    branches: [ develop ]
  workflow_dispatch:

env:
  AWS_REGION: us-east-1
  EKS_CLUSTER: self-healing-platform-staging

jobs:
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2
    
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: self-healing-platform
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:staging
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:staging
    
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --name ${{ env.EKS_CLUSTER }} --region ${{ env.AWS_REGION }}
    
    - name: Deploy to Kubernetes
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: self-healing-platform
        IMAGE_TAG: ${{ github.sha }}
      run: |
        kubectl set image deployment/self-healing-platform \
          platform=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
          -n self-healing-platform
        
        kubectl rollout status deployment/self-healing-platform -n self-healing-platform
    
    - name: Run smoke tests
      run: |
        STAGING_URL=$(kubectl get svc self-healing-platform-service -n self-healing-platform -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
        curl -f http://$STAGING_URL/health || exit 1
    
    - name: Notify Slack
      if: always()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'Staging deployment ${{ job.status }}'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

**File: `.github/workflows/cd-production.yml`**

```yaml
name: CD - Deploy to Production

on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy'
        required: true

env:
  AWS_REGION: us-east-1
  EKS_CLUSTER: self-healing-platform-cluster

jobs:
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2
    
    - name: Get version
      id: version
      run: |
        if [ "${{ github.event_name }}" == "push" ]; then
          echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
        else
          echo "VERSION=${{ github.event.inputs.version }}" >> $GITHUB_OUTPUT
        fi
    
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: self-healing-platform
        VERSION: ${{ steps.version.outputs.VERSION }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$VERSION .
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$VERSION $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$VERSION
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
    
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --name ${{ env.EKS_CLUSTER }} --region ${{ env.AWS_REGION }}
    
    - name: Create backup
      run: |
        kubectl get all -n self-healing-platform -o yaml > backup-$(date +%Y%m%d-%H%M%S).yaml
    
    - name: Deploy to Kubernetes (Blue-Green)
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: self-healing-platform
        VERSION: ${{ steps.version.outputs.VERSION }}
      run: |
        # Create green deployment
        kubectl set image deployment/self-healing-platform \
          platform=$ECR_REGISTRY/$ECR_REPOSITORY:$VERSION \
          -n self-healing-platform
        
        # Wait for rollout
        kubectl rollout status deployment/self-healing-platform -n self-healing-platform --timeout=5m
    
    - name: Run production smoke tests
      run: |
        PROD_URL=$(kubectl get svc self-healing-platform-service -n self-healing-platform -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
        
        # Health check
        curl -f http://$PROD_URL/health || exit 1
        
        # API check
        curl -f http://$PROD_URL/api/v1/status || exit 1
    
    - name: Rollback on failure
      if: failure()
      run: |
        kubectl rollout undo deployment/self-healing-platform -n self-healing-platform
    
    - name: Create GitHub Release
      if: success() && github.event_name == 'push'
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ steps.version.outputs.VERSION }}
        release_name: Release ${{ steps.version.outputs.VERSION }}
        body: |
          Production deployment of version ${{ steps.version.outputs.VERSION }}
          
          ## Changes
          See commit history for details.
    
    - name: Notify Slack
      if: always()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'Production deployment ${{ job.status }} - Version ${{ steps.version.outputs.VERSION }}'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 7. AUTOMATED TESTING SUITE

### 7.1 Test Structure

```bash
mkdir -p tests/{unit,integration,e2e,performance}
```

**File: `tests/conftest.py`**

```python
"""
Pytest Configuration and Fixtures
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_metrics():
    """Sample metrics data"""
    return {
        'timestamp': '2026-01-01T12:00:00',
        'cpu_usage': 65.0,
        'memory_usage': 70.0,
        'response_time': 250.0,
        'error_rate': 1.5,
        'requests_per_sec': 120.0
    }

@pytest.fixture
def anomaly_metrics():
    """Anomalous metrics data"""
    return {
        'timestamp': '2026-01-01T12:05:00',
        'cpu_usage': 95.0,
        'memory_usage': 88.0,
        'response_time': 1200.0,
        'error_rate': 8.5,
        'requests_per_sec': 50.0
    }
```

**File: `tests/integration/test_end_to_end.py`**

```python
"""
End-to-End Integration Tests
"""

import pytest
import requests
import time
from typing import Dict

BASE_URL = "http://localhost:8000"

class TestEndToEnd:
    """Test complete platform workflow"""
    
    def test_platform_health(self):
        """Test platform is healthy"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'
    
    def test_metrics_ingestion(self, sample_metrics):
        """Test metrics can be ingested"""
        response = requests.post(
            f"{BASE_URL}/api/v1/metrics",
            json=sample_metrics
        )
        assert response.status_code == 200
    
    def test_anomaly_detection_flow(self, anomaly_metrics):
        """Test anomaly detection and healing flow"""
        # 1. Ingest normal metrics
        for _ in range(10):
            requests.post(
                f"{BASE_URL}/api/v1/metrics",
                json={**sample_metrics, 'timestamp': '2026-01-01T12:00:00'}
            )
        
        time.sleep(2)
        
        # 2. Ingest anomalous metric
        response = requests.post(
            f"{BASE_URL}/api/v1/metrics",
            json=anomaly_metrics
        )
        assert response.status_code == 200
        
        time.sleep(5)
        
        # 3. Check anomalies were detected
        anomalies = requests.get(f"{BASE_URL}/api/v1/anomalies").json()
        assert len(anomalies) > 0
        
        # 4. Check healing actions were triggered
        healing = requests.get(f"{BASE_URL}/api/v1/healing-actions").json()
        assert len(healing) > 0
        assert healing[-1]['status'] in ['completed', 'executing']
    
    def test_dashboard_accessibility(self):
        """Test dashboard is accessible"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        assert 'Self-Healing Platform' in response.text
    
    def test_api_performance(self):
        """Test API response times"""
        endpoints = [
            '/api/v1/status',
            '/api/v1/metrics',
            '/api/v1/anomalies',
            '/api/v1/healing-actions'
        ]
        
        for endpoint in endpoints:
            start = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}")
            duration = time.time() - start
            
            assert response.status_code == 200
            assert duration < 1.0  # Response within 1 second
```

---

*This is Part 2. Would you like me to continue with:*
- **Part 3**: Monitoring & Observability (Prometheus + Grafana)
- **Part 4**: Complete Deployment Scripts
- **Part 5**: Testing & Validation Procedures

Which section should I create next?
