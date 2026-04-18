# After running deploy-all.sh, it checks:
if ! sudo k3s kubectl get svc prometheus-server -n monitoring; then
  echo 'Prometheus not found, installing...'
  
  # Installs Helm if missing
  # Adds Prometheus repo
  # Installs Prometheus with correct settings
  
  helm install prometheus prometheus-community/prometheus \
    --namespace monitoring \
    --set server.service.type=NodePort \
    --set server.service.nodePort=30090 \
    --set alertmanager.enabled=false \
    --set server.persistentVolume.enabled=false \
    --set kube-state-metrics.enabled=true
fi

# Then patches AI platform config
sudo k3s kubectl patch configmap ai-platform-config -n monitoring-demo \
  --type=merge -p '{"data":{"PROMETHEUS_ENABLED":"true"}}'

# Then restarts AI platform
sudo k3s kubectl rollout restart deployment/ai-platform -n monitoring-demo