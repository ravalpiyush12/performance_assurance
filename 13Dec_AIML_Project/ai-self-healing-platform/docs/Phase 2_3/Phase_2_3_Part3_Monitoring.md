# PHASE 2 & 3 IMPLEMENTATION - PART 3
## Monitoring & Observability (Prometheus + Grafana)

---

## TABLE OF CONTENTS

1. [Prometheus Setup](#1-prometheus-setup)
2. [Grafana Setup](#2-grafana-setup)
3. [Custom Metrics Export](#3-custom-metrics-export)
4. [Alert Configuration](#4-alert-configuration)
5. [Dashboard Creation](#5-dashboard-creation)

---

## 1. PROMETHEUS SETUP

### 1.1 Prometheus Configuration

**File: `monitoring/prometheus/prometheus.yml`**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'self-healing-platform'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
      timeout: 10s

# Load rules once and periodically evaluate them
rule_files:
  - 'alerts.yml'
  - 'recording-rules.yml'

# Scrape configurations
scrape_configs:
  # Platform application metrics
  - job_name: 'self-healing-platform'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - self-healing-platform
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: self-healing-platform
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_ip]
        target_label: pod_ip
    metrics_path: /metrics
    scheme: http

  # Kubernetes API server
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

  # Kubernetes nodes
  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

  # Kubernetes pods
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name

  # Kubernetes services
  - job_name: 'kubernetes-services'
    kubernetes_sd_configs:
      - role: service
    metrics_path: /probe
    params:
      module: [http_2xx]
    relabel_configs:
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_probe]
        action: keep
        regex: true
      - source_labels: [__address__]
        target_label: __param_target
      - target_label: __address__
        replacement: blackbox-exporter:9115
      - source_labels: [__param_target]
        target_label: instance
      - action: labelmap
        regex: __meta_kubernetes_service_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_service_name]
        target_label: kubernetes_name
```

**File: `monitoring/prometheus/alerts.yml`**

```yaml
groups:
  - name: platform_health
    interval: 30s
    rules:
      # CPU Alerts
      - alert: HighCPUUsage
        expr: cpu_usage > 80
        for: 2m
        labels:
          severity: warning
          component: platform
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value }}% on {{ $labels.pod }} for 2 minutes"
          runbook_url: "https://docs.platform.com/runbooks/high-cpu"

      - alert: CriticalCPUUsage
        expr: cpu_usage > 90
        for: 1m
        labels:
          severity: critical
          component: platform
        annotations:
          summary: "Critical CPU usage detected"
          description: "CPU usage is {{ $value }}% on {{ $labels.pod }}"

      # Memory Alerts
      - alert: HighMemoryUsage
        expr: memory_usage > 85
        for: 2m
        labels:
          severity: warning
          component: platform
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value }}% on {{ $labels.pod }} for 2 minutes"

      - alert: CriticalMemoryUsage
        expr: memory_usage > 95
        for: 1m
        labels:
          severity: critical
          component: platform
        annotations:
          summary: "Critical memory usage detected"
          description: "Memory usage is {{ $value }}% on {{ $labels.pod }}"

      # Response Time Alerts
      - alert: HighResponseTime
        expr: response_time > 800
        for: 2m
        labels:
          severity: warning
          component: platform
        annotations:
          summary: "High response time detected"
          description: "Response time is {{ $value }}ms on {{ $labels.pod }}"

      - alert: CriticalResponseTime
        expr: response_time > 2000
        for: 1m
        labels:
          severity: critical
          component: platform
        annotations:
          summary: "Critical response time detected"
          description: "Response time is {{ $value }}ms on {{ $labels.pod }}"

      # Error Rate Alerts
      - alert: HighErrorRate
        expr: error_rate > 5
        for: 1m
        labels:
          severity: warning
          component: platform
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}% on {{ $labels.pod }}"

      - alert: CriticalErrorRate
        expr: error_rate > 10
        for: 30s
        labels:
          severity: critical
          component: platform
        annotations:
          summary: "Critical error rate detected"
          description: "Error rate is {{ $value }}% on {{ $labels.pod }}"

  - name: ml_model
    interval: 30s
    rules:
      # Anomaly Detection Alerts
      - alert: AnomalyDetected
        expr: increase(anomalies_detected_total[5m]) > 0
        labels:
          severity: warning
          component: ml
        annotations:
          summary: "Anomaly detected by ML model"
          description: "{{ $value }} anomalies detected in last 5 minutes"

      - alert: HighAnomalyRate
        expr: rate(anomalies_detected_total[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
          component: ml
        annotations:
          summary: "High anomaly detection rate"
          description: "Anomaly rate is {{ $value }} per second"

      # ML Model Performance
      - alert: LowModelAccuracy
        expr: ml_model_accuracy < 0.85
        for: 5m
        labels:
          severity: warning
          component: ml
        annotations:
          summary: "ML model accuracy degraded"
          description: "Model accuracy is {{ $value }} (below 85%)"

      - alert: HighFalsePositiveRate
        expr: ml_false_positive_rate > 0.15
        for: 5m
        labels:
          severity: warning
          component: ml
        annotations:
          summary: "High false positive rate"
          description: "False positive rate is {{ $value }} (above 15%)"

  - name: self_healing
    interval: 30s
    rules:
      # Healing Action Alerts
      - alert: HealingActionFailed
        expr: increase(healing_actions_failed_total[5m]) > 0
        labels:
          severity: critical
          component: orchestrator
        annotations:
          summary: "Self-healing action failed"
          description: "{{ $value }} healing actions failed in last 5 minutes"

      - alert: HighHealingActionRate
        expr: rate(healing_actions_total[10m]) > 1
        for: 5m
        labels:
          severity: warning
          component: orchestrator
        annotations:
          summary: "High healing action rate"
          description: "System is healing frequently ({{ $value }} actions/sec)"

      - alert: HealingActionStuck
        expr: healing_action_duration_seconds > 300
        labels:
          severity: critical
          component: orchestrator
        annotations:
          summary: "Healing action taking too long"
          description: "Healing action has been running for {{ $value }}s"

  - name: kubernetes
    interval: 30s
    rules:
      # Pod Alerts
      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: critical
          component: kubernetes
        annotations:
          summary: "Pod is crash looping"
          description: "Pod {{ $labels.pod }} is restarting frequently"

      - alert: PodNotReady
        expr: kube_pod_status_phase{phase!="Running"} == 1
        for: 5m
        labels:
          severity: warning
          component: kubernetes
        annotations:
          summary: "Pod not ready"
          description: "Pod {{ $labels.pod }} has been not ready for 5 minutes"

      # Node Alerts
      - alert: NodeNotReady
        expr: kube_node_status_condition{condition="Ready",status="true"} == 0
        for: 5m
        labels:
          severity: critical
          component: kubernetes
        annotations:
          summary: "Node not ready"
          description: "Node {{ $labels.node }} is not ready"

      # HPA Alerts
      - alert: HPAMaxedOut
        expr: kube_hpa_status_current_replicas >= kube_hpa_spec_max_replicas
        for: 10m
        labels:
          severity: warning
          component: kubernetes
        annotations:
          summary: "HPA at maximum replicas"
          description: "HPA {{ $labels.hpa }} has reached max replicas"

  - name: system_health
    interval: 30s
    rules:
      # Overall Health
      - alert: SystemHealthDegraded
        expr: system_health_score < 80
        for: 5m
        labels:
          severity: warning
          component: platform
        annotations:
          summary: "System health degraded"
          description: "System health score is {{ $value }}% (below 80%)"

      - alert: SystemHealthCritical
        expr: system_health_score < 60
        for: 2m
        labels:
          severity: critical
          component: platform
        annotations:
          summary: "System health critical"
          description: "System health score is {{ $value }}% (below 60%)"

      # Uptime
      - alert: LowSystemUptime
        expr: system_uptime_seconds < 300
        labels:
          severity: info
          component: platform
        annotations:
          summary: "System recently restarted"
          description: "System uptime is only {{ $value }} seconds"
```

**File: `monitoring/prometheus/recording-rules.yml`**

```yaml
groups:
  - name: platform_aggregations
    interval: 30s
    rules:
      # CPU aggregations
      - record: cpu_usage:avg_5m
        expr: avg_over_time(cpu_usage[5m])
      
      - record: cpu_usage:max_5m
        expr: max_over_time(cpu_usage[5m])
      
      - record: cpu_usage:p95_5m
        expr: histogram_quantile(0.95, rate(cpu_usage_bucket[5m]))

      # Memory aggregations
      - record: memory_usage:avg_5m
        expr: avg_over_time(memory_usage[5m])
      
      - record: memory_usage:max_5m
        expr: max_over_time(memory_usage[5m])

      # Response time aggregations
      - record: response_time:avg_5m
        expr: avg_over_time(response_time[5m])
      
      - record: response_time:p50_5m
        expr: histogram_quantile(0.50, rate(response_time_bucket[5m]))
      
      - record: response_time:p95_5m
        expr: histogram_quantile(0.95, rate(response_time_bucket[5m]))
      
      - record: response_time:p99_5m
        expr: histogram_quantile(0.99, rate(response_time_bucket[5m]))

      # Error rate aggregations
      - record: error_rate:avg_5m
        expr: avg_over_time(error_rate[5m])
      
      - record: error_rate:rate_5m
        expr: rate(error_rate[5m])

      # Throughput
      - record: requests:rate_5m
        expr: rate(requests_total[5m])
      
      - record: requests:sum_5m
        expr: sum(rate(requests_total[5m]))

      # Anomaly rates
      - record: anomalies:rate_5m
        expr: rate(anomalies_detected_total[5m])
      
      - record: anomalies:count_1h
        expr: increase(anomalies_detected_total[1h])

      # Healing action rates
      - record: healing_actions:rate_5m
        expr: rate(healing_actions_total[5m])
      
      - record: healing_actions:success_rate
        expr: rate(healing_actions_succeeded_total[5m]) / rate(healing_actions_total[5m])

      # System health
      - record: system_health:avg_5m
        expr: avg_over_time(system_health_score[5m])
```

### 1.2 Prometheus Kubernetes Deployment

**File: `kubernetes/monitoring/prometheus-deployment.yaml`**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources:
      - nodes
      - nodes/proxy
      - services
      - endpoints
      - pods
    verbs: ["get", "list", "watch"]
  - apiGroups:
      - extensions
    resources:
      - ingresses
    verbs: ["get", "list", "watch"]
  - nonResourceURLs: ["/metrics"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
  - kind: ServiceAccount
    name: prometheus
    namespace: monitoring
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    # [Copy content from monitoring/prometheus/prometheus.yml]
  
  alerts.yml: |
    # [Copy content from monitoring/prometheus/alerts.yml]
  
  recording-rules.yml: |
    # [Copy content from monitoring/prometheus/recording-rules.yml]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
  labels:
    app: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      serviceAccountName: prometheus
      containers:
        - name: prometheus
          image: prom/prometheus:v2.48.0
          args:
            - '--config.file=/etc/prometheus/prometheus.yml'
            - '--storage.tsdb.path=/prometheus'
            - '--storage.tsdb.retention.time=15d'
            - '--web.console.libraries=/etc/prometheus/console_libraries'
            - '--web.console.templates=/etc/prometheus/consoles'
            - '--web.enable-lifecycle'
          ports:
            - containerPort: 9090
              name: web
          volumeMounts:
            - name: config
              mountPath: /etc/prometheus
            - name: storage
              mountPath: /prometheus
          resources:
            requests:
              cpu: 500m
              memory: 2Gi
            limits:
              cpu: 2000m
              memory: 4Gi
          livenessProbe:
            httpGet:
              path: /-/healthy
              port: 9090
            initialDelaySeconds: 30
            timeoutSeconds: 5
          readinessProbe:
            httpGet:
              path: /-/ready
              port: 9090
            initialDelaySeconds: 5
            timeoutSeconds: 5
      volumes:
        - name: config
          configMap:
            name: prometheus-config
        - name: storage
          persistentVolumeClaim:
            claimName: prometheus-storage
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-storage
  namespace: monitoring
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: standard
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
  labels:
    app: prometheus
spec:
  type: ClusterIP
  ports:
    - port: 9090
      targetPort: 9090
      protocol: TCP
      name: web
  selector:
    app: prometheus
```

---

## 2. GRAFANA SETUP

### 2.1 Grafana Configuration

**File: `monitoring/grafana/provisioning/datasources/prometheus.yaml`**

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus.monitoring.svc.cluster.local:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: 15s
      queryTimeout: 60s
```

**File: `monitoring/grafana/provisioning/dashboards/dashboards.yaml`**

```yaml
apiVersion: 1

providers:
  - name: 'Self-Healing Platform'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

### 2.2 Grafana Dashboard - Platform Overview

**File: `monitoring/grafana/dashboards/platform-overview.json`**

```json
{
  "dashboard": {
    "title": "Self-Healing Platform Overview",
    "uid": "platform-overview",
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 1,
    "refresh": "10s",
    "panels": [
      {
        "id": 1,
        "title": "System Health Score",
        "type": "gauge",
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "system_health_score",
            "legendFormat": "Health Score",
            "refId": "A"
          }
        ],
        "options": {
          "orientation": "auto",
          "showThresholdLabels": false,
          "showThresholdMarkers": true
        },
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 60, "color": "orange"},
                {"value": 80, "color": "yellow"},
                {"value": 90, "color": "green"}
              ]
            },
            "unit": "percent"
          }
        }
      },
      {
        "id": 2,
        "title": "CPU Usage",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 9, "x": 6, "y": 0},
        "targets": [
          {
            "expr": "cpu_usage",
            "legendFormat": "{{pod}}",
            "refId": "A"
          },
          {
            "expr": "avg(cpu_usage)",
            "legendFormat": "Average",
            "refId": "B"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "drawStyle": "line",
              "lineInterpolation": "smooth",
              "fillOpacity": 10
            },
            "min": 0,
            "max": 100,
            "unit": "percent",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 70, "color": "yellow"},
                {"value": 85, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Memory Usage",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 9, "x": 15, "y": 0},
        "targets": [
          {
            "expr": "memory_usage",
            "legendFormat": "{{pod}}",
            "refId": "A"
          },
          {
            "expr": "avg(memory_usage)",
            "legendFormat": "Average",
            "refId": "B"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "drawStyle": "line",
              "lineInterpolation": "smooth",
              "fillOpacity": 10
            },
            "min": 0,
            "max": 100,
            "unit": "percent",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 75, "color": "yellow"},
                {"value": 90, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 4,
        "title": "Response Time (P95)",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(response_time_bucket[5m]))",
            "legendFormat": "P95",
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.99, rate(response_time_bucket[5m]))",
            "legendFormat": "P99",
            "refId": "B"
          },
          {
            "expr": "avg_over_time(response_time[5m])",
            "legendFormat": "Average",
            "refId": "C"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "ms",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 500, "color": "yellow"},
                {"value": 1000, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 5,
        "title": "Error Rate",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "error_rate",
            "legendFormat": "{{pod}}",
            "refId": "A"
          },
          {
            "expr": "avg(error_rate)",
            "legendFormat": "Average",
            "refId": "B"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 3, "color": "yellow"},
                {"value": 5, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 6,
        "title": "Anomalies Detected",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 16},
        "targets": [
          {
            "expr": "increase(anomalies_detected_total[1h])",
            "legendFormat": "Last Hour",
            "refId": "A"
          }
        ],
        "options": {
          "colorMode": "value",
          "graphMode": "area",
          "justifyMode": "auto",
          "orientation": "auto",
          "reduceOptions": {
            "calcs": ["lastNotNull"],
            "fields": "",
            "values": false
          }
        },
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 5, "color": "yellow"},
                {"value": 10, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 7,
        "title": "Healing Actions",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 16},
        "targets": [
          {
            "expr": "increase(healing_actions_total[1h])",
            "legendFormat": "Last Hour",
            "refId": "A"
          }
        ],
        "options": {
          "colorMode": "value",
          "graphMode": "area"
        },
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 10, "color": "yellow"},
                {"value": 20, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 8,
        "title": "Healing Success Rate",
        "type": "gauge",
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 16},
        "targets": [
          {
            "expr": "rate(healing_actions_succeeded_total[5m]) / rate(healing_actions_total[5m]) * 100",
            "legendFormat": "Success Rate",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "unit": "percent",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 80, "color": "yellow"},
                {"value": 95, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "id": 9,
        "title": "ML Model Accuracy",
        "type": "gauge",
        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 16},
        "targets": [
          {
            "expr": "ml_model_accuracy * 100",
            "legendFormat": "Accuracy",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "unit": "percent",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 85, "color": "yellow"},
                {"value": 90, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "id": 10,
        "title": "Active Pods",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 20},
        "targets": [
          {
            "expr": "count(kube_pod_status_phase{namespace='self-healing-platform', phase='Running'})",
            "legendFormat": "Running Pods",
            "refId": "A"
          },
          {
            "expr": "kube_deployment_spec_replicas{namespace='self-healing-platform'}",
            "legendFormat": "Desired Replicas",
            "refId": "B"
          }
        ]
      },
      {
        "id": 11,
        "title": "Request Rate",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 20},
        "targets": [
          {
            "expr": "rate(requests_total[5m])",
            "legendFormat": "{{pod}}",
            "refId": "A"
          },
          {
            "expr": "sum(rate(requests_total[5m]))",
            "legendFormat": "Total",
            "refId": "B"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        }
      }
    ]
  }
}
```

### 2.3 Grafana Kubernetes Deployment

**File: `kubernetes/monitoring/grafana-deployment.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: monitoring
data:
  prometheus.yaml: |
    apiVersion: 1
    datasources:
      - name: Prometheus
        type: prometheus
        access: proxy
        url: http://prometheus.monitoring.svc.cluster.local:9090
        isDefault: true
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards-config
  namespace: monitoring
data:
  dashboards.yaml: |
    apiVersion: 1
    providers:
      - name: 'Self-Healing Platform'
        orgId: 1
        folder: ''
        type: file
        disableDeletion: false
        updateIntervalSeconds: 10
        allowUiUpdates: true
        options:
          path: /var/lib/grafana/dashboards
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: monitoring
data:
  platform-overview.json: |
    # [Copy content from monitoring/grafana/dashboards/platform-overview.json]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
        - name: grafana
          image: grafana/grafana:10.2.2
          ports:
            - containerPort: 3000
              name: http
          env:
            - name: GF_SECURITY_ADMIN_USER
              value: "admin"
            - name: GF_SECURITY_ADMIN_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: grafana-credentials
                  key: admin-password
            - name: GF_INSTALL_PLUGINS
              value: "grafana-piechart-panel,grafana-clock-panel"
          volumeMounts:
            - name: grafana-storage
              mountPath: /var/lib/grafana
            - name: grafana-datasources
              mountPath: /etc/grafana/provisioning/datasources
            - name: grafana-dashboards-config
              mountPath: /etc/grafana/provisioning/dashboards
            - name: grafana-dashboards
              mountPath: /var/lib/grafana/dashboards
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: 500m
              memory: 1Gi
          livenessProbe:
            httpGet:
              path: /api/health
              port: 3000
            initialDelaySeconds: 30
            timeoutSeconds: 5
          readinessProbe:
            httpGet:
              path: /api/health
              port: 3000
            initialDelaySeconds: 5
            timeoutSeconds: 5
      volumes:
        - name: grafana-storage
          persistentVolumeClaim:
            claimName: grafana-storage
        - name: grafana-datasources
          configMap:
            name: grafana-datasources
        - name: grafana-dashboards-config
          configMap:
            name: grafana-dashboards-config
        - name: grafana-dashboards
          configMap:
            name: grafana-dashboards
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: grafana-storage
  namespace: monitoring
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: monitoring
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 3000
      protocol: TCP
  selector:
    app: grafana
---
apiVersion: v1
kind: Secret
metadata:
  name: grafana-credentials
  namespace: monitoring
type: Opaque
stringData:
  admin-password: "admin123"  # Change this in production!
```

---

## 3. CUSTOM METRICS EXPORT

### 3.1 Prometheus Exporter for Platform

**File: `src/monitoring/prometheus_exporter.py`**

```python
"""
Prometheus Metrics Exporter
Exports platform metrics in Prometheus format
"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
from typing import Dict

# Define metrics
METRICS = {
    # Counters
    'requests_total': Counter(
        'requests_total',
        'Total number of requests',
        ['method', 'endpoint', 'status']
    ),
    'anomalies_detected_total': Counter(
        'anomalies_detected_total',
        'Total number of anomalies detected',
        ['anomaly_type', 'severity']
    ),
    'healing_actions_total': Counter(
        'healing_actions_total',
        'Total number of healing actions',
        ['action_type', 'status']
    ),
    'healing_actions_succeeded_total': Counter(
        'healing_actions_succeeded_total',
        'Total number of successful healing actions',
        ['action_type']
    ),
    'healing_actions_failed_total': Counter(
        'healing_actions_failed_total',
        'Total number of failed healing actions',
        ['action_type']
    ),
    
    # Gauges
    'cpu_usage': Gauge(
        'cpu_usage',
        'Current CPU usage percentage',
        ['pod']
    ),
    'memory_usage': Gauge(
        'memory_usage',
        'Current memory usage percentage',
        ['pod']
    ),
    'response_time': Gauge(
        'response_time',
        'Current response time in milliseconds',
        ['pod']
    ),
    'error_rate': Gauge(
        'error_rate',
        'Current error rate percentage',
        ['pod']
    ),
    'system_health_score': Gauge(
        'system_health_score',
        'Overall system health score (0-100)'
    ),
    'active_alerts': Gauge(
        'active_alerts',
        'Number of active alerts'
    ),
    'ml_model_accuracy': Gauge(
        'ml_model_accuracy',
        'ML model accuracy (0-1)'
    ),
    'ml_false_positive_rate': Gauge(
        'ml_false_positive_rate',
        'ML model false positive rate (0-1)'
    ),
    'system_uptime_seconds': Gauge(
        'system_uptime_seconds',
        'System uptime in seconds'
    ),
    
    # Histograms
    'response_time_histogram': Histogram(
        'response_time_histogram',
        'Response time histogram',
        ['endpoint'],
        buckets=[50, 100, 200, 500, 1000, 2000, 5000]
    ),
    'healing_action_duration_seconds': Histogram(
        'healing_action_duration_seconds',
        'Healing action duration in seconds',
        ['action_type'],
        buckets=[1, 5, 10, 30, 60, 120, 300]
    )
}

class PrometheusExporter:
    """
    Prometheus metrics exporter
    """
    
    def __init__(self):
        self.metrics = METRICS
        self.start_time = time.time()
    
    def update_metric(self, metric_name: str, value: float, labels: Dict = None):
        """Update a metric value"""
        if metric_name not in self.metrics:
            return
        
        metric = self.metrics[metric_name]
        
        if labels:
            if isinstance(metric, (Counter, Gauge, Histogram)):
                metric.labels(**labels).set(value) if isinstance(metric, Gauge) else metric.labels(**labels).inc(value)
        else:
            if isinstance(metric, Gauge):
                metric.set(value)
            elif isinstance(metric, Counter):
                metric.inc(value)
    
    def record_request(self, method: str, endpoint: str, status: int):
        """Record an HTTP request"""
        self.metrics['requests_total'].labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
    
    def record_anomaly(self, anomaly_type: str, severity: str):
        """Record an anomaly detection"""
        self.metrics['anomalies_detected_total'].labels(
            anomaly_type=anomaly_type,
            severity=severity
        ).inc()
    
    def record_healing_action(self, action_type: str, success: bool, duration: float):
        """Record a healing action"""
        status = 'succeeded' if success else 'failed'
        
        self.metrics['healing_actions_total'].labels(
            action_type=action_type,
            status=status
        ).inc()
        
        if success:
            self.metrics['healing_actions_succeeded_total'].labels(
                action_type=action_type
            ).inc()
        else:
            self.metrics['healing_actions_failed_total'].labels(
                action_type=action_type
            ).inc()
        
        self.metrics['healing_action_duration_seconds'].labels(
            action_type=action_type
        ).observe(duration)
    
    def update_system_metrics(self, metrics_dict: Dict):
        """Update system metrics"""
        pod_name = metrics_dict.get('pod', 'unknown')
        
        if 'cpu_usage' in metrics_dict:
            self.metrics['cpu_usage'].labels(pod=pod_name).set(metrics_dict['cpu_usage'])
        
        if 'memory_usage' in metrics_dict:
            self.metrics['memory_usage'].labels(pod=pod_name).set(metrics_dict['memory_usage'])
        
        if 'response_time' in metrics_dict:
            self.metrics['response_time'].labels(pod=pod_name).set(metrics_dict['response_time'])
        
        if 'error_rate' in metrics_dict:
            self.metrics['error_rate'].labels(pod=pod_name).set(metrics_dict['error_rate'])
    
    def update_health_score(self, score: float):
        """Update system health score"""
        self.metrics['system_health_score'].set(score)
    
    def update_ml_metrics(self, accuracy: float, false_positive_rate: float):
        """Update ML model metrics"""
        self.metrics['ml_model_accuracy'].set(accuracy)
        self.metrics['ml_false_positive_rate'].set(false_positive_rate)
    
    def update_uptime(self):
        """Update system uptime"""
        uptime = time.time() - self.start_time
        self.metrics['system_uptime_seconds'].set(uptime)
    
    def get_metrics(self) -> Response:
        """Get metrics in Prometheus format"""
        self.update_uptime()
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )


# Singleton instance
prometheus_exporter = PrometheusExporter()
```

### 3.2 Integration with FastAPI

**Add to `src/api/main.py`:**

```python
from src.monitoring.prometheus_exporter import prometheus_exporter

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return prometheus_exporter.get_metrics()

# Middleware for request tracking
@app.middleware("http")
async def track_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    prometheus_exporter.record_request(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    )
    
    prometheus_exporter.metrics['response_time_histogram'].labels(
        endpoint=request.url.path
    ).observe(duration * 1000)  # Convert to ms
    
    return response

# Update metrics when anomaly detected
async def process_metric(metric: Dict):
    # ... existing code ...
    
    if anomaly:
        prometheus_exporter.record_anomaly(
            anomaly_type=anomaly['anomaly_type'],
            severity=anomaly['severity']
        )
        
        # Update ML metrics
        if anomaly_detector.is_trained:
            prometheus_exporter.update_ml_metrics(
                accuracy=0.94,  # Get from detector
                false_positive_rate=0.078
            )
    
    # Update system metrics
    prometheus_exporter.update_system_metrics({
        'pod': os.getenv('POD_NAME', 'unknown'),
        'cpu_usage': metric['cpu_usage'],
        'memory_usage': metric['memory_usage'],
        'response_time': metric['response_time'],
        'error_rate': metric['error_rate']
    })
    
    # Update health score
    health_score = calculate_health_score()
    prometheus_exporter.update_health_score(health_score)
```

---

## 4. DEPLOYMENT SCRIPT

**File: `scripts/deploy_monitoring.sh`**

```bash
#!/bin/bash
set -e

echo "📊 Deploying Monitoring Stack (Prometheus + Grafana)"
echo "===================================================="

# Create monitoring namespace
kubectl apply -f kubernetes/monitoring/prometheus-deployment.yaml
kubectl apply -f kubernetes/monitoring/grafana-deployment.yaml

# Wait for deployments
echo "⏳ Waiting for Prometheus to be ready..."
kubectl wait --for=condition=ready pod \
    -l app=prometheus \
    -n monitoring \
    --timeout=300s

echo "⏳ Waiting for Grafana to be ready..."
kubectl wait --for=condition=ready pod \
    -l app=grafana \
    -n monitoring \
    --timeout=300s

echo "✅ Monitoring stack deployed successfully!"
echo ""
echo "🌐 Access Grafana:"
kubectl get svc grafana -n monitoring

echo ""
echo "📝 Default Grafana credentials:"
echo "  Username: admin"
echo "  Password: admin123 (change this!)"
```

---

*This completes Part 3. Would you like me to continue with Part 4 (Complete Deployment Scripts) and Part 5 (Testing & Validation Procedures)?*
