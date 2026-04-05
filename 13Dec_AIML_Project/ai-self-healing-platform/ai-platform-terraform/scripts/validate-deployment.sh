#!/bin/bash
# AI Self-Healing Platform - Deployment Validation Script
# Run this on master node after terraform apply completes

set -e

MASTER_IP=$(curl -s http://checkip.amazonaws.com)
PASSED=0
FAILED=0

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   AI SELF-HEALING PLATFORM - DEPLOYMENT VALIDATION             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Test function
test_check() {
    local test_name="$1"
    local test_command="$2"
    local expected="$3"
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" | grep -q "$expected"; then
        echo "✅ PASS"
        ((PASSED++))
        return 0
    else
        echo "❌ FAIL"
        ((FAILED++))
        return 1
    fi
}

echo "═══ CLUSTER HEALTH ═══"
echo ""

# Test 1: Both nodes ready
test_check "Master node ready" \
    "sudo k3s kubectl get nodes -o wide | grep master" \
    "Ready"

test_check "Worker node ready" \
    "sudo k3s kubectl get nodes -o wide | grep worker" \
    "Ready"

# Test 2: Metrics-server working
test_check "Metrics-server operational" \
    "sudo k3s kubectl top nodes 2>&1" \
    "master"

echo ""
echo "═══ POD STATUS ═══"
echo ""

# Test 3: AI Platform running
test_check "AI Platform pod running" \
    "sudo k3s kubectl get pods -n monitoring-demo | grep ai-platform" \
    "Running"

# Test 4: Sample App pods running
SAMPLE_APP_COUNT=$(sudo k3s kubectl get pods -n monitoring-demo | grep sample-app | grep Running | wc -l)
if [ "$SAMPLE_APP_COUNT" -ge 2 ]; then
    echo "Testing: Sample App pods running (count >= 2)... ✅ PASS ($SAMPLE_APP_COUNT pods)"
    ((PASSED++))
else
    echo "Testing: Sample App pods running (count >= 2)... ❌ FAIL ($SAMPLE_APP_COUNT pods)"
    ((FAILED++))
fi

# Test 5: Pod distribution
MASTER_PODS=$(sudo k3s kubectl get pods -n monitoring-demo -o wide | grep master | wc -l)
WORKER_PODS=$(sudo k3s kubectl get pods -n monitoring-demo -o wide | grep worker | wc -l)
if [ "$MASTER_PODS" -ge 1 ] && [ "$WORKER_PODS" -ge 1 ]; then
    echo "Testing: Pods distributed across nodes... ✅ PASS (Master: $MASTER_PODS, Worker: $WORKER_PODS)"
    ((PASSED++))
else
    echo "Testing: Pods distributed across nodes... ❌ FAIL (Master: $MASTER_PODS, Worker: $WORKER_PODS)"
    ((FAILED++))
fi

echo ""
echo "═══ SERVICES ═══"
echo ""

# Test 6: Services created
test_check "AI Platform service exists" \
    "sudo k3s kubectl get svc -n monitoring-demo | grep ai-platform" \
    "NodePort"

test_check "Sample App service exists" \
    "sudo k3s kubectl get svc -n monitoring-demo | grep sample-app" \
    "NodePort"

test_check "Prometheus service exists" \
    "sudo k3s kubectl get svc -n monitoring | grep prometheus-server" \
    "NodePort"

echo ""
echo "═══ HPA STATUS ═══"
echo ""

# Test 7: HPA configured
test_check "HPA exists" \
    "sudo k3s kubectl get hpa -n monitoring-demo" \
    "sample-app"

# Test 8: HPA showing metrics (may take 60-90 seconds)
echo -n "Testing: HPA showing CPU metrics... "
HPA_CPU=$(sudo k3s kubectl get hpa -n monitoring-demo -o jsonpath='{.items[0].status.currentMetrics[0].resource.current.averageUtilization}' 2>/dev/null || echo "unknown")
if [ "$HPA_CPU" != "unknown" ] && [ "$HPA_CPU" != "" ]; then
    echo "✅ PASS (CPU: ${HPA_CPU}%)"
    ((PASSED++))
else
    echo "⚠️  WAIT (Wait 60s for metrics to populate)"
    echo "   Run: sudo k3s kubectl get hpa -n monitoring-demo"
fi

echo ""
echo "═══ API ENDPOINTS ═══"
echo ""

# Test 9: Dashboard API responding
echo -n "Testing: AI Platform API responding... "
if curl -s -f http://localhost:30800/api/v1/status > /dev/null 2>&1; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL"
    ((FAILED++))
fi

# Test 10: Sample App responding
echo -n "Testing: Sample App responding... "
if curl -s -f http://localhost:30080/health > /dev/null 2>&1; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL"
    ((FAILED++))
fi

# Test 11: Prometheus responding
echo -n "Testing: Prometheus responding... "
if curl -s -f http://localhost:30090/-/healthy > /dev/null 2>&1; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL"
    ((FAILED++))
fi

echo ""
echo "═══ CONFIGURATION ═══"
echo ""

# Test 12: ConfigMap has required values
test_check "Prometheus enabled in ConfigMap" \
    "sudo k3s kubectl get configmap ai-platform-config -n monitoring-demo -o yaml" \
    "PROMETHEUS_ENABLED.*true"

test_check "Kubernetes enabled in ConfigMap" \
    "sudo k3s kubectl get configmap ai-platform-config -n monitoring-demo -o yaml" \
    "KUBERNETES_ENABLED.*true"

echo ""
echo "═══ PLATFORM STATUS ═══"
echo ""

# Test 13: Platform status check
PLATFORM_STATUS=$(curl -s http://localhost:30800/api/v1/status)

echo -n "Testing: Prometheus connected... "
if echo "$PLATFORM_STATUS" | jq -e '.prometheus_enabled == true' > /dev/null 2>&1; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL"
    ((FAILED++))
fi

echo -n "Testing: Kubernetes enabled... "
if echo "$PLATFORM_STATUS" | jq -e '.kubernetes_enabled == true' > /dev/null 2>&1; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL"
    ((FAILED++))
fi

echo -n "Testing: ML Model trained... "
if echo "$PLATFORM_STATUS" | jq -e '.ml_model_trained == true' > /dev/null 2>&1; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "⚠️  WAIT (Model trains after ~20 metric samples)"
fi

echo -n "Testing: Health Score >= 85%... "
HEALTH_SCORE=$(echo "$PLATFORM_STATUS" | jq -r '.health_score // 0')
if (( $(echo "$HEALTH_SCORE >= 85" | bc -l) )); then
    echo "✅ PASS (${HEALTH_SCORE}%)"
    ((PASSED++))
else
    echo "⚠️  LOW (${HEALTH_SCORE}%)"
fi

echo ""
echo "═══ EXTERNAL ACCESS ═══"
echo ""

echo "Dashboard:  http://${MASTER_IP}:30800"
echo "Sample App: http://${MASTER_IP}:30080/health"
echo "Prometheus: http://${MASTER_IP}:30090"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   VALIDATION RESULTS                                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Tests Passed: $PASSED"
echo "Tests Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED! 🎉"
    echo ""
    echo "Your AI Self-Healing Platform is ready for demonstration!"
    echo ""
    echo "Next steps:"
    echo "1. Open dashboard: http://${MASTER_IP}:30800"
    echo "2. Run load test: ./load-test.ps1 -MasterIP \"${MASTER_IP}\""
    echo "3. Watch self-healing in action!"
    echo ""
    exit 0
else
    echo "⚠️  SOME TESTS FAILED ⚠️"
    echo ""
    echo "Common fixes:"
    echo "1. Wait 2-3 minutes for all pods to fully start"
    echo "2. Wait 90 seconds for HPA metrics to populate"
    echo "3. Check logs: sudo k3s kubectl logs -n monitoring-demo -l app=ai-platform"
    echo "4. Restart failed pods: sudo k3s kubectl rollout restart deployment/<name> -n monitoring-demo"
    echo ""
    echo "For detailed troubleshooting, see TROUBLESHOOTING.md"
    echo ""
    exit 1
fi
