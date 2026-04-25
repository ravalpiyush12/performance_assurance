#!/bin/bash

echo "=========================================="
echo "GUARANTEED CPU SCALE-UP TEST"
echo "=========================================="

# Step 1: Generate HEAVY sustained load
echo ""
echo "1. Generating HEAVY CPU load..."
timeout 120s bash -c 'while true; do
    for i in {1..30}; do
        curl -s http://localhost:30080/compute > /dev/null 2>&1 &
    done
    sleep 0.5
done' &

LOAD_PID=$!

# Step 2: Watch for the action
echo "2. Monitoring for scale-up action (60s)..."
sleep 60

# Step 3: Check what happened
echo ""
echo "3. === Current Metrics ==="
sudo k3s kubectl logs -l app=ai-platform -n monitoring-demo --tail=5 | grep "Prometheus →"

echo ""
echo "4. === Anomalies Detected ==="
curl -s http://localhost:30800/api/v1/anomalies?limit=5 | jq -r '.[] | "[\(.anomaly_type)] \(.anomaly_score) - \(.severity)"'

echo ""
echo "5. === Healing Actions ==="
curl -s http://localhost:30800/api/v1/healing-actions?limit=5 | jq -r '.[] | "[\(.action_type)] \(.description) - \(.status)"'

echo ""
echo "6. === Pod Count ==="
kubectl get pods -n monitoring-demo -l app=sample-app --no-headers | wc -l

echo ""
echo "7. === Detailed Logs ==="
sudo k3s kubectl logs -l app=ai-platform -n monitoring-demo --tail=100 | grep -E "ANOMALY DETECTED|Action decided|KUBERNETES SCALING"

# Cleanup
kill $LOAD_PID 2>/dev/null
wait $LOAD_PID 2>/dev/null

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="