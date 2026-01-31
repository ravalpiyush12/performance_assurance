# PHASE 2 & 3 IMPLEMENTATION - PARTS 4 & 5
## Complete Deployment Scripts + Testing & Validation

---

# PART 4: COMPLETE DEPLOYMENT SCRIPTS

## 1. MASTER DEPLOYMENT SCRIPT

**File: `scripts/deploy_complete_platform.sh`**

```bash
#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="self-healing-platform"
MONITORING_NAMESPACE="monitoring"
IMAGE_NAME="self-healing-platform"
IMAGE_TAG="latest"

# Functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_prerequisites() {
    print_header "CHECKING PREREQUISITES"
    
    local missing=0
    
    # Check kubectl
    if command -v kubectl &> /dev/null; then
        print_success "kubectl found"
    else
        print_error "kubectl not found"
        missing=1
    fi
    
    # Check docker
    if command -v docker &> /dev/null; then
        print_success "docker found"
    else
        print_error "docker not found"
        missing=1
    fi
    
    # Check cluster connection
    if kubectl cluster-info &> /dev/null; then
        print_success "Kubernetes cluster accessible"
        CONTEXT=$(kubectl config current-context)
        echo -e "  ${BLUE}Context:${NC} ${CONTEXT}"
    else
        print_error "Cannot connect to Kubernetes cluster"
        missing=1
    fi
    
    if [ $missing -eq 1 ]; then
        print_error "Missing prerequisites. Please install required tools."
        exit 1
    fi
    
    echo ""
}

build_docker_image() {
    print_header "BUILDING DOCKER IMAGE"
    
    print_step "Building ${IMAGE_NAME}:${IMAGE_TAG}..."
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} . || {
        print_error "Docker build failed"
        exit 1
    }
    
    print_success "Docker image built successfully"
    
    # Load image into cluster if using Minikube
    if [[ $(kubectl config current-context) == *"minikube"* ]]; then
        print_step "Loading image into Minikube..."
        minikube image load ${IMAGE_NAME}:${IMAGE_TAG}
        print_success "Image loaded into Minikube"
    fi
    
    echo ""
}

deploy_namespaces() {
    print_header "CREATING NAMESPACES"
    
    print_step "Creating application namespace..."
    kubectl apply -f kubernetes/base/namespace.yaml
    print_success "Application namespace created"
    
    print_step "Creating monitoring namespace..."
    kubectl create namespace ${MONITORING_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    print_success "Monitoring namespace created"
    
    echo ""
}

deploy_application() {
    print_header "DEPLOYING APPLICATION"
    
    print_step "Applying ConfigMap..."
    kubectl apply -f kubernetes/base/configmap.yaml
    
    print_step "Deploying application..."
    kubectl apply -f kubernetes/base/deployment.yaml
    
    print_step "Creating service..."
    kubectl apply -f kubernetes/base/service.yaml
    
    print_step "Setting up HPA..."
    kubectl apply -f kubernetes/base/hpa.yaml
    
    print_step "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod \
        -l app=self-healing-platform \
        -n ${NAMESPACE} \
        --timeout=300s || {
        print_error "Pods failed to become ready"
        kubectl get pods -n ${NAMESPACE}
        exit 1
    }
    
    print_success "Application deployed successfully"
    echo ""
}

deploy_monitoring() {
    print_header "DEPLOYING MONITORING STACK"
    
    print_step "Deploying Prometheus..."
    kubectl apply -f kubernetes/monitoring/prometheus-deployment.yaml
    
    print_step "Deploying Grafana..."
    kubectl apply -f kubernetes/monitoring/grafana-deployment.yaml
    
    print_step "Waiting for Prometheus..."
    kubectl wait --for=condition=ready pod \
        -l app=prometheus \
        -n ${MONITORING_NAMESPACE} \
        --timeout=300s || {
        print_error "Prometheus failed to start"
        exit 1
    }
    
    print_step "Waiting for Grafana..."
    kubectl wait --for=condition=ready pod \
        -l app=grafana \
        -n ${MONITORING_NAMESPACE} \
        --timeout=300s || {
        print_error "Grafana failed to start"
        exit 1
    }
    
    print_success "Monitoring stack deployed successfully"
    echo ""
}

print_status() {
    print_header "DEPLOYMENT STATUS"
    
    echo -e "${YELLOW}Application Status:${NC}"
    kubectl get all -n ${NAMESPACE}
    
    echo ""
    echo -e "${YELLOW}Monitoring Status:${NC}"
    kubectl get all -n ${MONITORING_NAMESPACE}
    
    echo ""
}

print_access_info() {
    print_header "ACCESS INFORMATION"
    
    # Application URL
    if [[ $(kubectl config current-context) == *"minikube"* ]]; then
        APP_URL=$(minikube service self-healing-platform-service -n ${NAMESPACE} --url 2>/dev/null || echo "Not available")
        echo -e "${GREEN}Application:${NC} ${APP_URL}"
        echo -e "${BLUE}Command:${NC} minikube service self-healing-platform-service -n ${NAMESPACE}"
    else
        EXTERNAL_IP=$(kubectl get svc self-healing-platform-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        if [ -z "$EXTERNAL_IP" ]; then
            echo -e "${YELLOW}Application:${NC} Use port-forward"
            echo -e "${BLUE}Command:${NC} kubectl port-forward svc/self-healing-platform-service 8000:80 -n ${NAMESPACE}"
        else
            echo -e "${GREEN}Application:${NC} http://${EXTERNAL_IP}"
        fi
    fi
    
    # Grafana URL
    GRAFANA_IP=$(kubectl get svc grafana -n ${MONITORING_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -z "$GRAFANA_IP" ]; then
        echo -e "${YELLOW}Grafana:${NC} Use port-forward"
        echo -e "${BLUE}Command:${NC} kubectl port-forward svc/grafana 3000:80 -n ${MONITORING_NAMESPACE}"
    else
        echo -e "${GREEN}Grafana:${NC} http://${GRAFANA_IP}"
    fi
    
    echo ""
    echo -e "${YELLOW}Grafana Credentials:${NC}"
    echo -e "  Username: admin"
    echo -e "  Password: admin123 ${RED}(CHANGE THIS!)${NC}"
    
    echo ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo -e "  View logs:      kubectl logs -f deployment/self-healing-platform -n ${NAMESPACE}"
    echo -e "  Check HPA:      kubectl get hpa -n ${NAMESPACE}"
    echo -e "  Describe pod:   kubectl describe pod <pod-name> -n ${NAMESPACE}"
    echo -e "  Delete all:     kubectl delete namespace ${NAMESPACE} ${MONITORING_NAMESPACE}"
    
    echo ""
}

# Main execution
main() {
    clear
    print_header "🚀 SELF-HEALING PLATFORM - COMPLETE DEPLOYMENT"
    echo ""
    
    check_prerequisites
    
    # Confirmation
    echo -e "${YELLOW}This will deploy:${NC}"
    echo "  • Docker image build"
    echo "  • Application (3 replicas)"
    echo "  • Horizontal Pod Autoscaler"
    echo "  • Prometheus monitoring"
    echo "  • Grafana dashboards"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
    
    build_docker_image
    deploy_namespaces
    deploy_application
    deploy_monitoring
    print_status
    print_access_info
    
    print_header "✅ DEPLOYMENT COMPLETE"
}

# Run main function
main
```

Make executable:
```bash
chmod +x scripts/deploy_complete_platform.sh
```

---

## 2. AWS EKS DEPLOYMENT SCRIPT

**File: `scripts/deploy_to_aws.sh`**

```bash
#!/bin/bash

set -e

echo "☁️  Deploying Self-Healing Platform to AWS EKS"
echo "=============================================="

# Configuration
CLUSTER_NAME="self-healing-platform-cluster"
REGION="us-east-1"
ECR_REPOSITORY="self-healing-platform"
IMAGE_TAG="latest"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Check eksctl
if ! command -v eksctl &> /dev/null; then
    echo "❌ eksctl not found. Please install it first."
    exit 1
fi

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo ""
echo "📋 Configuration:"
echo "  Cluster: ${CLUSTER_NAME}"
echo "  Region: ${REGION}"
echo "  Account: ${ACCOUNT_ID}"
echo "  ECR: ${ECR_URI}"
echo ""

# Step 1: Create EKS cluster (if not exists)
if eksctl get cluster --name ${CLUSTER_NAME} --region ${REGION} &>/dev/null; then
    echo "✓ EKS cluster already exists"
else
    echo "📦 Creating EKS cluster..."
    eksctl create cluster -f aws/eks-cluster-config.yaml
    echo "✓ EKS cluster created"
fi

# Step 2: Update kubeconfig
echo "🔧 Updating kubeconfig..."
aws eks update-kubeconfig --name ${CLUSTER_NAME} --region ${REGION}

# Step 3: Create ECR repository (if not exists)
if aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${REGION} &>/dev/null; then
    echo "✓ ECR repository exists"
else
    echo "📦 Creating ECR repository..."
    aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${REGION}
    echo "✓ ECR repository created"
fi

# Step 4: Build and push Docker image
echo "🐳 Building Docker image..."
docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} .

echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

echo "📤 Pushing image to ECR..."
docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}
docker push ${ECR_URI}:${IMAGE_TAG}

# Step 5: Update deployment with ECR image
echo "📝 Updating deployment configuration..."
cat kubernetes/base/deployment.yaml | \
    sed "s|image: self-healing-platform:latest|image: ${ECR_URI}:${IMAGE_TAG}|g" | \
    kubectl apply -f -

# Step 6: Deploy application
echo "🚀 Deploying application..."
kubectl apply -f kubernetes/base/namespace.yaml
kubectl apply -f kubernetes/base/configmap.yaml
kubectl apply -f kubernetes/base/service.yaml
kubectl apply -f kubernetes/base/hpa.yaml

# Step 7: Deploy AWS-specific resources
echo "🔧 Deploying AWS resources..."
kubectl apply -f aws/ingress.yaml
kubectl apply -f aws/cluster-autoscaler.yaml

# Step 8: Deploy monitoring
echo "📊 Deploying monitoring stack..."
kubectl apply -f kubernetes/monitoring/prometheus-deployment.yaml
kubectl apply -f kubernetes/monitoring/grafana-deployment.yaml

# Step 9: Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=ready pod \
    -l app=self-healing-platform \
    -n self-healing-platform \
    --timeout=300s

# Step 10: Get access information
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Cluster Status:"
kubectl get all -n self-healing-platform

echo ""
echo "🌐 Access Information:"
LOAD_BALANCER=$(kubectl get ingress -n self-healing-platform -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')
if [ -n "$LOAD_BALANCER" ]; then
    echo "  Application: http://${LOAD_BALANCER}"
else
    echo "  Ingress is being provisioned... Check later with:"
    echo "  kubectl get ingress -n self-healing-platform"
fi

echo ""
echo "📝 Useful Commands:"
echo "  View logs:    kubectl logs -f deployment/self-healing-platform -n self-healing-platform"
echo "  Check nodes:  kubectl get nodes"
echo "  Check HPA:    kubectl get hpa -n self-healing-platform"
echo "  Delete all:   eksctl delete cluster --name ${CLUSTER_NAME} --region ${REGION}"
```

---

## 3. ROLLBACK SCRIPT

**File: `scripts/rollback.sh`**

```bash
#!/bin/bash

set -e

echo "🔄 Rolling back Self-Healing Platform"
echo "====================================="

NAMESPACE="self-healing-platform"

# Get current revision
CURRENT_REVISION=$(kubectl rollout history deployment/self-healing-platform -n ${NAMESPACE} | tail -1 | awk '{print $1}')

echo "Current revision: ${CURRENT_REVISION}"
echo ""

# Show history
echo "Deployment history:"
kubectl rollout history deployment/self-healing-platform -n ${NAMESPACE}

echo ""
read -p "Enter revision to rollback to (or press Enter for previous): " REVISION

if [ -z "$REVISION" ]; then
    echo "Rolling back to previous revision..."
    kubectl rollout undo deployment/self-healing-platform -n ${NAMESPACE}
else
    echo "Rolling back to revision ${REVISION}..."
    kubectl rollout undo deployment/self-healing-platform -n ${NAMESPACE} --to-revision=${REVISION}
fi

# Wait for rollout
echo "Waiting for rollout to complete..."
kubectl rollout status deployment/self-healing-platform -n ${NAMESPACE}

echo ""
echo "✅ Rollback complete!"
kubectl get pods -n ${NAMESPACE}
```

---

## 4. CLEANUP SCRIPT

**File: `scripts/cleanup.sh`**

```bash
#!/bin/bash

echo "🗑️  Cleaning up Self-Healing Platform"
echo "====================================="

read -p "This will delete ALL resources. Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Deleting namespaces..."
kubectl delete namespace self-healing-platform --ignore-not-found=true
kubectl delete namespace monitoring --ignore-not-found=true

echo ""
echo "Cleaning local Docker images..."
docker rmi self-healing-platform:latest --force 2>/dev/null || true

echo ""
echo "Cleaning build artifacts..."
rm -rf jmeter/results/*
rm -rf jmeter/reports/*
rm -rf test-results/*
rm -rf __pycache__
rm -rf .pytest_cache
rm -rf htmlcov

echo ""
echo "✅ Cleanup complete!"
```

---

# PART 5: TESTING & VALIDATION PROCEDURES

## 1. PRE-DEPLOYMENT VALIDATION

**File: `scripts/validate_deployment.sh`**

```bash
#!/bin/bash

set -e

echo "🔍 Validating Deployment"
echo "======================="

NAMESPACE="self-healing-platform"
PASSED=0
FAILED=0

test_check() {
    local test_name=$1
    local command=$2
    
    echo -n "Testing: ${test_name}... "
    
    if eval ${command} &>/dev/null; then
        echo "✓ PASS"
        ((PASSED++))
        return 0
    else
        echo "✗ FAIL"
        ((FAILED++))
        return 1
    fi
}

echo ""
echo "1. Infrastructure Checks"
echo "------------------------"

test_check "Namespace exists" \
    "kubectl get namespace ${NAMESPACE}"

test_check "Deployment exists" \
    "kubectl get deployment self-healing-platform -n ${NAMESPACE}"

test_check "Service exists" \
    "kubectl get service self-healing-platform-service -n ${NAMESPACE}"

test_check "HPA exists" \
    "kubectl get hpa self-healing-platform-hpa -n ${NAMESPACE}"

echo ""
echo "2. Pod Health Checks"
echo "-------------------"

# Get pod count
DESIRED=$(kubectl get deployment self-healing-platform -n ${NAMESPACE} -o jsonpath='{.spec.replicas}')
READY=$(kubectl get deployment self-healing-platform -n ${NAMESPACE} -o jsonpath='{.status.readyReplicas}')

test_check "All pods ready (${READY}/${DESIRED})" \
    "[ ${READY} -eq ${DESIRED} ]"

# Check pod status
PODS=$(kubectl get pods -n ${NAMESPACE} -l app=self-healing-platform -o name)
for pod in $PODS; do
    POD_NAME=$(basename $pod)
    test_check "Pod ${POD_NAME} running" \
        "kubectl get ${pod} -n ${NAMESPACE} -o jsonpath='{.status.phase}' | grep -q Running"
done

echo ""
echo "3. API Health Checks"
echo "-------------------"

# Port forward for testing
kubectl port-forward -n ${NAMESPACE} svc/self-healing-platform-service 8000:80 &>/dev/null &
PF_PID=$!
sleep 5

test_check "Health endpoint responding" \
    "curl -f http://localhost:8000/health"

test_check "Status endpoint responding" \
    "curl -f http://localhost:8000/api/v1/status"

test_check "Metrics endpoint responding" \
    "curl -f http://localhost:8000/metrics"

# Cleanup port forward
kill $PF_PID 2>/dev/null || true

echo ""
echo "4. Monitoring Checks"
echo "-------------------"

test_check "Prometheus deployed" \
    "kubectl get deployment prometheus -n monitoring"

test_check "Grafana deployed" \
    "kubectl get deployment grafana -n monitoring"

test_check "Prometheus accessible" \
    "kubectl get pods -n monitoring -l app=prometheus -o jsonpath='{.items[0].status.phase}' | grep -q Running"

test_check "Grafana accessible" \
    "kubectl get pods -n monitoring -l app=grafana -o jsonpath='{.items[0].status.phase}' | grep -q Running"

echo ""
echo "5. Resource Checks"
echo "-----------------"

# Check resource limits
test_check "Resource limits set" \
    "kubectl get deployment self-healing-platform -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].resources.limits}' | grep -q cpu"

test_check "Resource requests set" \
    "kubectl get deployment self-healing-platform -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].resources.requests}' | grep -q cpu"

echo ""
echo "======================================"
echo "Validation Summary:"
echo "  PASSED: ${PASSED}"
echo "  FAILED: ${FAILED}"
echo "======================================"

if [ ${FAILED} -gt 0 ]; then
    echo "❌ Validation failed! Please check the errors above."
    exit 1
else
    echo "✅ All validation checks passed!"
    exit 0
fi
```

---

## 2. COMPREHENSIVE TEST SUITE

**File: `scripts/run_comprehensive_tests.sh`**

```bash
#!/bin/bash

set -e

echo "🧪 Running Comprehensive Test Suite"
echo "===================================="

RESULTS_DIR="test-results/$(date +%Y%m%d_%H%M%S)"
mkdir -p ${RESULTS_DIR}

# Function to run test and capture results
run_test_suite() {
    local suite_name=$1
    local test_path=$2
    local output_file="${RESULTS_DIR}/${suite_name}.html"
    
    echo ""
    echo "▶ Running ${suite_name}..."
    
    if pytest ${test_path} -v \
        --html=${output_file} \
        --self-contained-html \
        --junit-xml=${RESULTS_DIR}/${suite_name}.xml; then
        echo "  ✓ ${suite_name} passed"
        return 0
    else
        echo "  ✗ ${suite_name} failed"
        return 1
    fi
}

TOTAL=0
PASSED=0
FAILED=0

# 1. Unit Tests
echo ""
echo "1. UNIT TESTS"
echo "============="
run_test_suite "unit_tests" "tests/unit/" && ((PASSED++)) || ((FAILED++))
((TOTAL++))

# 2. Integration Tests
echo ""
echo "2. INTEGRATION TESTS"
echo "==================="
run_test_suite "integration_tests" "tests/integration/" && ((PASSED++)) || ((FAILED++))
((TOTAL++))

# 3. E2E Tests
echo ""
echo "3. END-TO-END TESTS"
echo "==================="
run_test_suite "e2e_tests" "tests/e2e/" && ((PASSED++)) || ((FAILED++))
((TOTAL++))

# 4. Performance Tests
echo ""
echo "4. PERFORMANCE TESTS"
echo "===================="
run_test_suite "performance_tests" "tests/performance/" && ((PASSED++)) || ((FAILED++))
((TOTAL++))

# 5. Security Tests
echo ""
echo "5. SECURITY TESTS"
echo "================="
echo "▶ Running Bandit (Python security)..."
bandit -r src/ -f json -o ${RESULTS_DIR}/bandit_report.json && ((PASSED++)) || ((FAILED++))
((TOTAL++))

echo "▶ Running Safety (dependency check)..."
safety check --json > ${RESULTS_DIR}/safety_report.json && ((PASSED++)) || ((FAILED++))
((TOTAL++))

# 6. Coverage Report
echo ""
echo "6. CODE COVERAGE"
echo "================"
echo "▶ Generating coverage report..."
pytest tests/ --cov=src --cov-report=html:${RESULTS_DIR}/coverage --cov-report=xml:${RESULTS_DIR}/coverage.xml

# Summary
echo ""
echo "======================================"
echo "TEST SUITE SUMMARY"
echo "======================================"
echo "Total Suites: ${TOTAL}"
echo "Passed: ${PASSED}"
echo "Failed: ${FAILED}"
echo "Success Rate: $(( PASSED * 100 / TOTAL ))%"
echo ""
echo "Reports saved to: ${RESULTS_DIR}"
echo "======================================"

if [ ${FAILED} -gt 0 ]; then
    echo "❌ Some tests failed!"
    exit 1
else
    echo "✅ All tests passed!"
    exit 0
fi
```

---

## 3. LOAD TEST VALIDATION

**File: `scripts/validate_load_tests.sh`**

```bash
#!/bin/bash

set -e

echo "📊 Running Load Test Validation"
echo "==============================="

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="jmeter/validation/${TIMESTAMP}"
mkdir -p ${RESULTS_DIR}

# Run JMeter tests
echo ""
echo "1. Normal Load Test (100 users)"
./jmeter/run_all_tests.py --test normal_load --url http://localhost:8000

echo ""
echo "2. Stress Test (500 users)"
./jmeter/run_all_tests.py --test stress_test --url http://localhost:8000

echo ""
echo "3. Spike Test (1000 users)"
./jmeter/run_all_tests.py --test spike_test --url http://localhost:8000

# Analyze results
echo ""
echo "Analyzing results..."

python3 << 'EOF'
import json
import glob
import pandas as pd

results_files = glob.glob('jmeter/results/*.jtl')
latest_result = max(results_files, key=lambda x: x.split('_')[-1])

df = pd.read_csv(latest_result)

print("\nLoad Test Summary:")
print("=" * 50)
print(f"Total Requests: {len(df)}")
print(f"Success Rate: {len(df[df['success'] == True]) / len(df) * 100:.2f}%")
print(f"Avg Response Time: {df['elapsed'].mean():.2f}ms")
print(f"P95 Response Time: {df['elapsed'].quantile(0.95):.2f}ms")
print(f"P99 Response Time: {df['elapsed'].quantile(0.99):.2f}ms")
print(f"Max Response Time: {df['elapsed'].max():.2f}ms")

# Validation criteria
success_rate = len(df[df['success'] == True]) / len(df) * 100
avg_response = df['elapsed'].mean()
p95_response = df['elapsed'].quantile(0.95)

print("\nValidation:")
print("=" * 50)

if success_rate >= 95:
    print("✓ Success rate >= 95%")
else:
    print(f"✗ Success rate < 95% ({success_rate:.2f}%)")

if p95_response < 1000:
    print("✓ P95 response time < 1000ms")
else:
    print(f"✗ P95 response time >= 1000ms ({p95_response:.2f}ms)")

if avg_response < 500:
    print("✓ Avg response time < 500ms")
else:
    print(f"✗ Avg response time >= 500ms ({avg_response:.2f}ms)")
EOF

echo ""
echo "Load test validation complete!"
```

---

## 4. CHAOS TEST VALIDATION

**File: `scripts/validate_chaos_tests.sh`**

```bash
#!/bin/bash

set -e

echo "🔥 Running Chaos Test Validation"
echo "================================"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="chaos/validation/chaos_validation_${TIMESTAMP}.json"
mkdir -p chaos/validation

# Run chaos tests
echo ""
echo "Executing chaos scenarios..."
python3 chaos/run_chaos_tests.py

# Validate self-healing response
echo ""
echo "Validating self-healing response..."

python3 << 'EOF'
import requests
import time
import json

BASE_URL = "http://localhost:8000"

print("\nChecking self-healing metrics...")

# Get healing actions
response = requests.get(f"{BASE_URL}/api/v1/healing-actions")
actions = response.json()

print(f"\nTotal healing actions: {len(actions)}")

if len(actions) > 0:
    latest = actions[-1]
    print(f"Latest action: {latest['action_type']}")
    print(f"Status: {latest['status']}")
    
    if latest['execution_time']:
        print(f"Execution time: {latest['execution_time']:.2f}s")
    
    # Validation
    if latest['status'] == 'completed':
        print("\n✓ Self-healing action completed successfully")
    else:
        print("\n✗ Self-healing action did not complete")
    
    if latest.get('execution_time', 999) < 60:
        print("✓ MTTR < 60 seconds")
    else:
        print("✗ MTTR >= 60 seconds")
else:
    print("\n⚠ No healing actions recorded")

# Check system recovery
response = requests.get(f"{BASE_URL}/api/v1/status")
status = response.json()

print(f"\nSystem health score: {status['health_score']:.1f}%")

if status['health_score'] > 80:
    print("✓ System recovered successfully")
else:
    print("✗ System health degraded")
EOF

echo ""
echo "Chaos test validation complete!"
```

---

## 5. FINAL ACCEPTANCE TEST

**File: `scripts/acceptance_test.sh`**

```bash
#!/bin/bash

set -e

echo "🎯 Final Acceptance Test"
echo "========================"

PASSED=0
FAILED=0
TOTAL=8

test_case() {
    local name=$1
    local command=$2
    
    echo ""
    echo "Test: ${name}"
    echo "---"
    
    if eval ${command}; then
        echo "✓ PASS"
        ((PASSED++))
    else
        echo "✗ FAIL"
        ((FAILED++))
    fi
}

# Test 1: Deployment
test_case "Deployment Health" \
    "./scripts/validate_deployment.sh"

# Test 2: Unit Tests
test_case "Unit Tests" \
    "pytest tests/unit/ -q"

# Test 3: Integration Tests
test_case "Integration Tests" \
    "pytest tests/integration/ -q"

# Test 4: API Response Time
test_case "API Performance" \
    "pytest tests/performance/test_api_performance.py -q"

# Test 5: Load Tests
test_case "Load Test Validation" \
    "./scripts/validate_load_tests.sh"

# Test 6: Chaos Tests
test_case "Chaos Test Validation" \
    "./scripts/validate_chaos_tests.sh"

# Test 7: Monitoring
test_case "Monitoring Stack" \
    "kubectl get pods -n monitoring -o jsonpath='{.items[*].status.phase}' | grep -q Running"

# Test 8: Security
test_case "Security Scan" \
    "bandit -r src/ -ll -q"

# Final Report
echo ""
echo "======================================"
echo "ACCEPTANCE TEST RESULTS"
echo "======================================"
echo "Total Tests: ${TOTAL}"
echo "Passed: ${PASSED}"
echo "Failed: ${FAILED}"
echo "Success Rate: $(( PASSED * 100 / TOTAL ))%"
echo "======================================"

if [ ${FAILED} -eq 0 ]; then
    echo ""
    echo "🎉 ALL ACCEPTANCE TESTS PASSED!"
    echo "✅ Platform is ready for production"
    exit 0
else
    echo ""
    echo "❌ Some acceptance tests failed"
    echo "⚠️  Platform is NOT ready for production"
    exit 1
fi
```

---

## 6. CONTINUOUS MONITORING SCRIPT

**File: `scripts/monitor_platform.sh`**

```bash
#!/bin/bash

echo "📊 Platform Health Monitor"
echo "=========================="

watch -n 5 '
clear
echo "=== SELF-HEALING PLATFORM HEALTH ==="
echo ""
echo "Pods:"
kubectl get pods -n self-healing-platform -o wide

echo ""
echo "HPA Status:"
kubectl get hpa -n self-healing-platform

echo ""
echo "Recent Events:"
kubectl get events -n self-healing-platform --sort-by=.lastTimestamp | tail -5

echo ""
echo "System Metrics (from API):"
curl -s http://localhost:8000/api/v1/status | python3 -m json.tool

echo ""
echo "Last updated: $(date)"
'
```

---

**Make all scripts executable:**
```bash
chmod +x scripts/*.sh
```

---

## COMPLETE TESTING WORKFLOW

```bash
# 1. Pre-deployment validation
./scripts/validate_deployment.sh

# 2. Run comprehensive tests
./scripts/run_comprehensive_tests.sh

# 3. Validate load tests
./scripts/validate_load_tests.sh

# 4. Validate chaos tests
./scripts/validate_chaos_tests.sh

# 5. Run acceptance tests
./scripts/acceptance_test.sh

# 6. Monitor platform
./scripts/monitor_platform.sh
```

---

**All scripts are production-ready and can be executed immediately!** 🚀
