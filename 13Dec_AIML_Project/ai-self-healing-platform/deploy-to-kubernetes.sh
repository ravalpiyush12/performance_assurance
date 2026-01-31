#!/bin/bash

# ============================================================================
# Kubernetes Deployment Script
# Deploys the AI/ML Self-Healing Platform to Kubernetes
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="self-healing-platform"
IMAGE_NAME="self-healing-platform"
IMAGE_TAG=${1:-latest}

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  AI/ML Self-Healing Platform - Kubernetes Deployment${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    print_error "kubectl not found. Please install: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "docker not found. Please install: https://docs.docker.com/get-docker/"
    exit 1
fi

print_info "✓ kubectl $(kubectl version --client --short)"
print_info "✓ docker $(docker --version)"

# Check cluster connection
print_info "Checking cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster"
    print_error "Configure kubectl: aws eks update-kubeconfig --name <cluster-name>"
    exit 1
fi

CLUSTER_NAME=$(kubectl config current-context)
print_info "✓ Connected to cluster: ${CLUSTER_NAME}"

# Step 1: Create namespace
print_info "Step 1: Creating namespace..."
kubectl apply -f kubernetes/namespace.yaml
print_info "✓ Namespace created"

# Step 2: Build and push Docker image
print_info "Step 2: Building Docker image..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
print_info "✓ Image built: ${IMAGE_NAME}:${IMAGE_TAG}"

# If using ECR, push to ECR
if [[ ! -z "${ECR_REPOSITORY_URL}" ]]; then
    print_info "Pushing to ECR: ${ECR_REPOSITORY_URL}"
    
    # Login to ECR
    AWS_REGION=$(echo ${ECR_REPOSITORY_URL} | cut -d'.' -f4)
    aws ecr get-login-password --region ${AWS_REGION} | \
        docker login --username AWS --password-stdin ${ECR_REPOSITORY_URL}
    
    # Tag and push
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ECR_REPOSITORY_URL}:${IMAGE_TAG}
    docker push ${ECR_REPOSITORY_URL}:${IMAGE_TAG}
    
    print_info "✓ Image pushed to ECR"
    
    # Update deployment with ECR image
    export ECR_REPOSITORY_URL
    envsubst < kubernetes/deployment.yaml | kubectl apply -f -
else
    print_warn "ECR_REPOSITORY_URL not set, using local image"
    print_warn "For production, push image to a registry"
    kubectl apply -f kubernetes/deployment.yaml
fi

# Step 3: Apply ConfigMap and Secrets
print_info "Step 3: Creating ConfigMap and Secrets..."
kubectl apply -f kubernetes/configmap.yaml
print_info "✓ ConfigMap and Secrets created"

# Step 4: Deploy application
print_info "Step 4: Deploying application..."
kubectl apply -f kubernetes/deployment.yaml
print_info "✓ Deployment created"

# Step 5: Create service
print_info "Step 5: Creating service..."
kubectl apply -f kubernetes/service.yaml
print_info "✓ Service created"

# Step 6: Configure auto-scaling
print_info "Step 6: Configuring auto-scaling..."

# Check if metrics-server is installed
if ! kubectl get deployment metrics-server -n kube-system &> /dev/null; then
    print_warn "metrics-server not found"
    read -p "Install metrics-server? (y/n): " install_metrics
    if [[ $install_metrics == "y" ]]; then
        kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
        print_info "✓ metrics-server installed"
        print_info "Waiting for metrics-server to be ready..."
        kubectl wait --for=condition=available --timeout=60s deployment/metrics-server -n kube-system
    fi
fi

kubectl apply -f kubernetes/hpa.yaml
print_info "✓ HPA created"

# Step 7: Configure Ingress (optional)
if [[ -f kubernetes/ingress.yaml ]]; then
    read -p "Deploy Ingress? (y/n): " deploy_ingress
    if [[ $deploy_ingress == "y" ]]; then
        print_info "Step 7: Configuring Ingress..."
        kubectl apply -f kubernetes/ingress.yaml
        print_info "✓ Ingress created"
    fi
fi

# Step 8: Wait for deployment
print_info "Step 8: Waiting for deployment to be ready..."
kubectl rollout status deployment/self-healing-platform -n ${NAMESPACE} --timeout=300s

if [[ $? -eq 0 ]]; then
    print_info "✓ Deployment successful!"
else
    print_error "Deployment failed or timed out"
    exit 1
fi

# Display deployment information
echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Deployment Complete!${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Get pod status
print_info "Pod Status:"
kubectl get pods -n ${NAMESPACE}

echo ""

# Get service information
print_info "Service Information:"
kubectl get svc -n ${NAMESPACE}

echo ""

# Get external IP/hostname
EXTERNAL_IP=""
while [ -z $EXTERNAL_IP ]; do
    print_info "Waiting for external IP..."
    EXTERNAL_IP=$(kubectl get svc self-healing-platform -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(kubectl get svc self-healing-platform -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    fi
    [ -z "$EXTERNAL_IP" ] && sleep 5
done

echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}  Access Your Application${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo "  Dashboard: http://${EXTERNAL_IP}"
echo "  API:       http://${EXTERNAL_IP}/api/v1/status"
echo "  Health:    http://${EXTERNAL_IP}/health"
echo ""
echo -e "${GREEN}============================================================================${NC}"
echo ""

# Display useful commands
print_info "Useful Commands:"
echo ""
echo "  View logs:"
echo "    kubectl logs -f deployment/self-healing-platform -n ${NAMESPACE}"
echo ""
echo "  Check pod status:"
echo "    kubectl get pods -n ${NAMESPACE}"
echo ""
echo "  Describe pod:"
echo "    kubectl describe pod <pod-name> -n ${NAMESPACE}"
echo ""
echo "  Port forward (for local access):"
echo "    kubectl port-forward svc/self-healing-platform 8000:80 -n ${NAMESPACE}"
echo ""
echo "  Scale manually:"
echo "    kubectl scale deployment/self-healing-platform --replicas=5 -n ${NAMESPACE}"
echo ""
echo "  Delete deployment:"
echo "    kubectl delete namespace ${NAMESPACE}"
echo ""

print_info "Deployment script completed successfully! 🚀"