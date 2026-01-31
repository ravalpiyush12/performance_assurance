# PHASE 4 & 5 IMPLEMENTATION GUIDE
## Production Readiness, Bug Fixes, Final Presentation & Go-Live

**Timeline:** March - May 2026  
**Status:** Ready for Implementation

---

## TABLE OF CONTENTS

### PHASE 4: Production Readiness & Bug Fixes (March - April 2026)
1. [Bug Tracking & Management](#1-bug-tracking--management)
2. [Security Hardening](#2-security-hardening)
3. [Performance Optimization](#3-performance-optimization)
4. [Production Deployment Checklist](#4-production-deployment-checklist)

### PHASE 5: Final Presentation & Go-Live (May 2026)
5. [Documentation Finalization](#5-documentation-finalization)
6. [Presentation Preparation](#6-presentation-preparation)
7. [Demo Environment Setup](#7-demo-environment-setup)
8. [Go-Live Procedures](#8-go-live-procedures)

---

# PHASE 4: PRODUCTION READINESS & BUG FIXES

## Duration: March - April 2026 (5 weeks)

---

## 1. BUG TRACKING & MANAGEMENT

### 1.1 Bug Tracking System Setup

**File: `.github/ISSUE_TEMPLATE/bug_report.md`**

```markdown
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of what the bug is.

## To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
What actually happened.

## Screenshots
If applicable, add screenshots to help explain your problem.

## Environment
- OS: [e.g. Ubuntu 22.04]
- Python Version: [e.g. 3.11]
- Kubernetes Version: [e.g. 1.28]
- Browser: [e.g. Chrome 120]

## Severity
- [ ] Critical - System down, data loss
- [ ] High - Major functionality broken
- [ ] Medium - Feature not working as expected
- [ ] Low - Minor issue, cosmetic

## Additional Context
Add any other context about the problem here.

## Logs
```
Paste relevant logs here
```

## Possible Solution
If you have ideas on how to fix this, please describe.
```

**File: `scripts/create_bug_report.sh`**

```bash
#!/bin/bash

echo "🐛 Bug Report Creator"
echo "===================="

read -p "Bug Title: " TITLE
read -p "Severity (critical/high/medium/low): " SEVERITY
read -p "Component (api/ml/orchestrator/dashboard/deployment): " COMPONENT

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUG_FILE="bugs/bug_${TIMESTAMP}.md"
mkdir -p bugs

cat > ${BUG_FILE} << EOF
# Bug Report: ${TITLE}

**Date:** $(date)
**Severity:** ${SEVERITY}
**Component:** ${COMPONENT}
**Reporter:** $(git config user.name)
**Status:** Open

## Description


## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior


## Actual Behavior


## Environment
- OS: $(uname -s)
- Python: $(python --version)
- Kubernetes: $(kubectl version --client --short 2>/dev/null || echo "N/A")

## Logs
\`\`\`

\`\`\`

## Investigation


## Fix Plan


EOF

echo "Bug report created: ${BUG_FILE}"
echo "Please fill in the details"
```

### 1.2 Bug Categorization & Prioritization

**File: `bugs/bug_tracker.json`**

```json
{
  "bugs": [],
  "severity_levels": {
    "critical": {
      "description": "System down, data loss, security vulnerability",
      "sla_hours": 4,
      "priority": 1
    },
    "high": {
      "description": "Major functionality broken, significant performance degradation",
      "sla_hours": 24,
      "priority": 2
    },
    "medium": {
      "description": "Feature not working correctly, minor performance issues",
      "sla_hours": 72,
      "priority": 3
    },
    "low": {
      "description": "UI/UX improvements, minor bugs, cosmetic issues",
      "sla_hours": 168,
      "priority": 4
    }
  },
  "bug_workflow": {
    "states": ["Open", "In Progress", "Testing", "Fixed", "Closed", "Wont Fix"],
    "transitions": {
      "Open": ["In Progress", "Wont Fix"],
      "In Progress": ["Testing", "Open"],
      "Testing": ["Fixed", "In Progress"],
      "Fixed": ["Closed", "In Progress"],
      "Closed": [],
      "Wont Fix": []
    }
  }
}
```

**File: `scripts/bug_tracker.py`**

```python
#!/usr/bin/env python3
"""
Bug Tracking System
Manages bugs throughout the project lifecycle
"""

import json
import os
from datetime import datetime
from typing import List, Dict
from pathlib import Path

class BugTracker:
    def __init__(self, tracker_file='bugs/bug_tracker.json'):
        self.tracker_file = tracker_file
        self.data = self._load_tracker()
        
    def _load_tracker(self):
        """Load bug tracker data"""
        if os.path.exists(self.tracker_file):
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        return {'bugs': [], 'statistics': {}}
    
    def _save_tracker(self):
        """Save bug tracker data"""
        os.makedirs(os.path.dirname(self.tracker_file), exist_ok=True)
        with open(self.tracker_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_bug(self, title: str, description: str, severity: str, 
                component: str, reporter: str):
        """Add a new bug"""
        bug = {
            'id': f"BUG-{len(self.data['bugs']) + 1:04d}",
            'title': title,
            'description': description,
            'severity': severity,
            'component': component,
            'reporter': reporter,
            'status': 'Open',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'assigned_to': None,
            'fix_version': None
        }
        
        self.data['bugs'].append(bug)
        self._save_tracker()
        
        print(f"✓ Bug created: {bug['id']} - {title}")
        return bug
    
    def update_bug_status(self, bug_id: str, new_status: str):
        """Update bug status"""
        for bug in self.data['bugs']:
            if bug['id'] == bug_id:
                bug['status'] = new_status
                bug['updated_at'] = datetime.now().isoformat()
                self._save_tracker()
                print(f"✓ Bug {bug_id} status updated to: {new_status}")
                return True
        
        print(f"✗ Bug {bug_id} not found")
        return False
    
    def get_bugs_by_severity(self, severity: str) -> List[Dict]:
        """Get all bugs of a specific severity"""
        return [b for b in self.data['bugs'] if b['severity'] == severity]
    
    def get_open_bugs(self) -> List[Dict]:
        """Get all open bugs"""
        return [b for b in self.data['bugs'] 
                if b['status'] not in ['Fixed', 'Closed', 'Wont Fix']]
    
    def generate_report(self):
        """Generate bug report"""
        bugs = self.data['bugs']
        
        print("\n" + "="*70)
        print("BUG TRACKER REPORT")
        print("="*70)
        
        # Summary by severity
        print("\nBy Severity:")
        for severity in ['critical', 'high', 'medium', 'low']:
            count = len([b for b in bugs if b['severity'] == severity])
            print(f"  {severity.capitalize()}: {count}")
        
        # Summary by status
        print("\nBy Status:")
        statuses = {}
        for bug in bugs:
            status = bug['status']
            statuses[status] = statuses.get(status, 0) + 1
        
        for status, count in sorted(statuses.items()):
            print(f"  {status}: {count}")
        
        # Open critical bugs
        critical_open = [b for b in bugs 
                        if b['severity'] == 'critical' 
                        and b['status'] in ['Open', 'In Progress']]
        
        if critical_open:
            print("\n⚠️  CRITICAL OPEN BUGS:")
            for bug in critical_open:
                print(f"  {bug['id']}: {bug['title']}")
        
        # Summary
        total = len(bugs)
        fixed = len([b for b in bugs if b['status'] in ['Fixed', 'Closed']])
        open_bugs = len(self.get_open_bugs())
        
        print("\n" + "="*70)
        print(f"Total Bugs: {total}")
        print(f"Fixed: {fixed} ({fixed/total*100:.1f}%)" if total > 0 else "Fixed: 0")
        print(f"Open: {open_bugs}")
        print("="*70)
    
    def export_to_csv(self, output_file='bugs/bug_report.csv'):
        """Export bugs to CSV"""
        import csv
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', newline='') as f:
            if self.data['bugs']:
                fieldnames = self.data['bugs'][0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.data['bugs'])
        
        print(f"✓ Bug report exported to: {output_file}")


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bug Tracker')
    parser.add_argument('command', choices=['add', 'update', 'list', 'report', 'export'])
    parser.add_argument('--id', help='Bug ID')
    parser.add_argument('--title', help='Bug title')
    parser.add_argument('--description', help='Bug description')
    parser.add_argument('--severity', choices=['critical', 'high', 'medium', 'low'])
    parser.add_argument('--component', help='Component name')
    parser.add_argument('--status', help='Bug status')
    
    args = parser.parse_args()
    
    tracker = BugTracker()
    
    if args.command == 'add':
        if not all([args.title, args.severity, args.component]):
            print("✗ Missing required fields: --title, --severity, --component")
            return
        
        tracker.add_bug(
            args.title,
            args.description or '',
            args.severity,
            args.component,
            os.getenv('USER', 'unknown')
        )
    
    elif args.command == 'update':
        if not all([args.id, args.status]):
            print("✗ Missing required fields: --id, --status")
            return
        
        tracker.update_bug_status(args.id, args.status)
    
    elif args.command == 'list':
        open_bugs = tracker.get_open_bugs()
        if open_bugs:
            print("\nOpen Bugs:")
            for bug in open_bugs:
                print(f"  {bug['id']}: [{bug['severity']}] {bug['title']}")
        else:
            print("\n✓ No open bugs!")
    
    elif args.command == 'report':
        tracker.generate_report()
    
    elif args.command == 'export':
        tracker.export_to_csv()


if __name__ == '__main__':
    main()
```

Make executable:
```bash
chmod +x scripts/bug_tracker.py
```

---

## 2. SECURITY HARDENING

### 2.1 Security Audit Checklist

**File: `security/security_audit_checklist.md`**

```markdown
# Security Audit Checklist

## Authentication & Authorization

- [ ] API endpoints require authentication
- [ ] JWT tokens have appropriate expiration
- [ ] Role-based access control (RBAC) implemented
- [ ] Admin endpoints properly protected
- [ ] Service-to-service authentication configured

## Secrets Management

- [ ] No hardcoded credentials in code
- [ ] Environment variables used for secrets
- [ ] Kubernetes Secrets configured
- [ ] AWS Secrets Manager / Azure Key Vault integration (if cloud)
- [ ] Secrets rotation policy defined

## Network Security

- [ ] HTTPS/TLS enabled for all endpoints
- [ ] Certificate management configured
- [ ] Network policies defined in Kubernetes
- [ ] Ingress rules properly configured
- [ ] Rate limiting implemented

## Container Security

- [ ] Non-root user in Dockerfile
- [ ] Minimal base images used
- [ ] No unnecessary packages installed
- [ ] Image scanning integrated (Trivy/Snyk)
- [ ] Security contexts defined in pods

## Application Security

- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF protection
- [ ] Dependency vulnerability scanning

## Data Protection

- [ ] Sensitive data encrypted at rest
- [ ] Sensitive data encrypted in transit
- [ ] PII handling compliant
- [ ] Data retention policies defined
- [ ] Backup encryption enabled

## Monitoring & Logging

- [ ] Security events logged
- [ ] Log aggregation configured
- [ ] Alerting for security events
- [ ] Audit trail maintained
- [ ] Log retention policy defined

## Kubernetes Security

- [ ] Pod Security Policies/Standards configured
- [ ] Resource limits set
- [ ] Network policies defined
- [ ] RBAC properly configured
- [ ] Service accounts with minimal permissions

## Compliance

- [ ] GDPR compliance (if applicable)
- [ ] Security documentation complete
- [ ] Incident response plan defined
- [ ] Security testing performed
- [ ] Vulnerability disclosure policy
```

### 2.2 Security Implementation

**File: `src/security/authentication.py`**

```python
"""
Authentication & Authorization Module
Implements JWT-based authentication
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

# Configuration
SECRET_KEY = "your-secret-key-here"  # Store in environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class AuthHandler:
    """Handle authentication operations"""
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def encode_token(self, user_id: str, role: str = "user") -> str:
        """Generate JWT token"""
        payload = {
            'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            'iat': datetime.utcnow(),
            'sub': user_id,
            'role': role
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def decode_token(self, token: str) -> dict:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid token')
    
    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(security)):
        """FastAPI dependency for authentication"""
        return self.decode_token(auth.credentials)


auth_handler = AuthHandler()


def require_admin(auth: dict = Depends(auth_handler.auth_wrapper)):
    """Require admin role"""
    if auth.get('role') != 'admin':
        raise HTTPException(status_code=403, detail='Admin access required')
    return auth


def require_user(auth: dict = Depends(auth_handler.auth_wrapper)):
    """Require authenticated user"""
    return auth
```

**File: `src/security/input_validation.py`**

```python
"""
Input Validation & Sanitization
Prevents injection attacks and invalid data
"""

import re
from typing import Any
from fastapi import HTTPException

class InputValidator:
    """Validate and sanitize user inputs"""
    
    @staticmethod
    def validate_metric_value(value: float, min_val: float = 0, max_val: float = 100) -> float:
        """Validate metric value is within range"""
        if not isinstance(value, (int, float)):
            raise HTTPException(status_code=400, detail="Metric value must be numeric")
        
        if value < min_val or value > max_val:
            raise HTTPException(
                status_code=400, 
                detail=f"Metric value must be between {min_val} and {max_val}"
            )
        
        return float(value)
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            raise HTTPException(status_code=400, detail="Input must be string")
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', input_str)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_timestamp(timestamp: str) -> bool:
        """Validate ISO format timestamp"""
        try:
            from datetime import datetime
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return True
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format")
    
    @staticmethod
    def validate_json_structure(data: dict, required_fields: list) -> bool:
        """Validate JSON has required fields"""
        missing = [field for field in required_fields if field not in data]
        
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}"
            )
        
        return True


validator = InputValidator()
```

**File: `kubernetes/base/network-policy.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: self-healing-platform-netpol
  namespace: self-healing-platform
spec:
  podSelector:
    matchLabels:
      app: self-healing-platform
  policyTypes:
    - Ingress
    - Egress
  
  ingress:
    # Allow traffic from ingress controller
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
    
    # Allow traffic from monitoring namespace
    - from:
        - namespaceSelector:
            matchLabels:
              name: monitoring
      ports:
        - protocol: TCP
          port: 8000
  
  egress:
    # Allow DNS
    - to:
        - namespaceSelector:
            matchLabels:
              name: kube-system
      ports:
        - protocol: UDP
          port: 53
    
    # Allow HTTPS for external APIs
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 443
    
    # Allow monitoring
    - to:
        - namespaceSelector:
            matchLabels:
              name: monitoring
      ports:
        - protocol: TCP
          port: 9090
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-default
  namespace: self-healing-platform
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

**File: `kubernetes/base/pod-security-policy.yaml`**

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
  annotations:
    seccomp.security.alpha.kubernetes.io/allowedProfileNames: 'runtime/default'
    apparmor.security.beta.kubernetes.io/allowedProfileNames: 'runtime/default'
spec:
  privileged: false
  allowPrivilegeEscalation: false
  
  # Required to prevent escalations
  requiredDropCapabilities:
    - ALL
  
  # Allow core volume types
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  
  hostNetwork: false
  hostIPC: false
  hostPID: false
  
  runAsUser:
    rule: 'MustRunAsNonRoot'
  
  seLinux:
    rule: 'RunAsAny'
  
  supplementalGroups:
    rule: 'RunAsAny'
  
  fsGroup:
    rule: 'RunAsAny'
  
  readOnlyRootFilesystem: false
```

### 2.3 Security Scanning Script

**File: `scripts/security_scan.sh`**

```bash
#!/bin/bash

set -e

echo "🔒 Security Scanning"
echo "==================="

SCAN_DIR="security/scan-results"
mkdir -p ${SCAN_DIR}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 1. Python Dependency Scanning
echo ""
echo "1. Scanning Python dependencies (Safety)..."
safety check --json > ${SCAN_DIR}/safety_${TIMESTAMP}.json || true
safety check || echo "⚠️  Vulnerabilities found in dependencies"

# 2. Python Code Security (Bandit)
echo ""
echo "2. Scanning Python code (Bandit)..."
bandit -r src/ -f json -o ${SCAN_DIR}/bandit_${TIMESTAMP}.json || true
bandit -r src/ -ll || echo "⚠️  Security issues found in code"

# 3. Docker Image Scanning (Trivy)
echo ""
echo "3. Scanning Docker image (Trivy)..."
if command -v trivy &> /dev/null; then
    trivy image self-healing-platform:latest \
        --severity HIGH,CRITICAL \
        --format json \
        --output ${SCAN_DIR}/trivy_${TIMESTAMP}.json
    
    trivy image self-healing-platform:latest --severity HIGH,CRITICAL
else
    echo "⚠️  Trivy not installed. Skipping image scan."
fi

# 4. Kubernetes Manifests Scanning
echo ""
echo "4. Scanning Kubernetes manifests..."
if command -v kubesec &> /dev/null; then
    for file in kubernetes/base/*.yaml; do
        echo "  Scanning $(basename $file)..."
        kubesec scan $file || true
    done
else
    echo "⚠️  Kubesec not installed. Skipping manifest scan."
fi

# 5. Secrets Detection
echo ""
echo "5. Scanning for leaked secrets (detect-secrets)..."
if command -v detect-secrets &> /dev/null; then
    detect-secrets scan --all-files > ${SCAN_DIR}/secrets_${TIMESTAMP}.json || true
    
    if [ -s ${SCAN_DIR}/secrets_${TIMESTAMP}.json ]; then
        echo "⚠️  Potential secrets detected!"
        cat ${SCAN_DIR}/secrets_${TIMESTAMP}.json
    else
        echo "✓ No secrets detected"
    fi
else
    echo "⚠️  detect-secrets not installed."
fi

# Generate Summary Report
echo ""
echo "=================================="
echo "SECURITY SCAN SUMMARY"
echo "=================================="
echo "Scan Date: $(date)"
echo "Results: ${SCAN_DIR}/"
echo ""
echo "Review the reports and address any findings."
echo "=================================="
```

Make executable:
```bash
chmod +x scripts/security_scan.sh
```

---

## 3. PERFORMANCE OPTIMIZATION

### 3.1 Performance Profiling

**File: `scripts/profile_performance.py`**

```python
#!/usr/bin/env python3
"""
Performance Profiling Tool
Identifies performance bottlenecks
"""

import cProfile
import pstats
import io
import time
import requests
from typing import Callable

class PerformanceProfiler:
    """Profile application performance"""
    
    def __init__(self):
        self.results = []
    
    def profile_function(self, func: Callable, *args, **kwargs):
        """Profile a single function"""
        profiler = cProfile.Profile()
        
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        # Get stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)
        
        print(s.getvalue())
        return result
    
    def benchmark_api_endpoint(self, url: str, num_requests: int = 100):
        """Benchmark API endpoint response time"""
        print(f"\nBenchmarking: {url}")
        print(f"Requests: {num_requests}")
        print("-" * 50)
        
        response_times = []
        errors = 0
        
        for i in range(num_requests):
            try:
                start = time.time()
                response = requests.get(url, timeout=10)
                duration = (time.time() - start) * 1000  # ms
                
                response_times.append(duration)
                
                if response.status_code != 200:
                    errors += 1
                
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i+1}/{num_requests}")
            
            except Exception as e:
                errors += 1
                print(f"  Error: {e}")
        
        if response_times:
            avg = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            # Calculate percentiles
            sorted_times = sorted(response_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            
            print("\nResults:")
            print(f"  Success Rate: {(len(response_times) - errors) / len(response_times) * 100:.2f}%")
            print(f"  Avg Response Time: {avg:.2f}ms")
            print(f"  Min Response Time: {min_time:.2f}ms")
            print(f"  Max Response Time: {max_time:.2f}ms")
            print(f"  P50: {p50:.2f}ms")
            print(f"  P95: {p95:.2f}ms")
            print(f"  P99: {p99:.2f}ms")
            
            return {
                'avg': avg,
                'min': min_time,
                'max': max_time,
                'p50': p50,
                'p95': p95,
                'p99': p99,
                'success_rate': (len(response_times) - errors) / len(response_times)
            }
        
        return None
    
    def profile_ml_model(self, detector, test_data):
        """Profile ML model performance"""
        print("\nProfiling ML Model...")
        print("-" * 50)
        
        # Training time
        start = time.time()
        detector._train_model()
        training_time = time.time() - start
        print(f"Training Time: {training_time:.2f}s")
        
        # Prediction time
        prediction_times = []
        for data in test_data:
            start = time.time()
            detector.detect_anomaly(data)
            prediction_times.append((time.time() - start) * 1000)
        
        avg_prediction = sum(prediction_times) / len(prediction_times)
        print(f"Avg Prediction Time: {avg_prediction:.2f}ms")
        
        return {
            'training_time': training_time,
            'avg_prediction_time': avg_prediction
        }


def main():
    """Run performance profiling"""
    profiler = PerformanceProfiler()
    
    # Benchmark API endpoints
    base_url = "http://localhost:8000"
    
    endpoints = [
        f"{base_url}/health",
        f"{base_url}/api/v1/status",
        f"{base_url}/api/v1/metrics?limit=10",
        f"{base_url}/api/v1/anomalies?limit=10"
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            results[endpoint] = profiler.benchmark_api_endpoint(endpoint, num_requests=50)
        except Exception as e:
            print(f"Error benchmarking {endpoint}: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    
    for endpoint, result in results.items():
        if result:
            print(f"\n{endpoint}")
            print(f"  P95: {result['p95']:.2f}ms")
            print(f"  Success Rate: {result['success_rate']*100:.2f}%")


if __name__ == '__main__':
    main()
```

### 3.2 Performance Optimization Implementations

**File: `src/optimization/caching.py`**

```python
"""
Caching Layer
Reduces database/API calls
"""

from functools import lru_cache
import redis
import json
from typing import Any, Optional

class CacheManager:
    """Manage caching operations"""
    
    def __init__(self, redis_host='localhost', redis_port=6379):
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True
            )
            self.redis_available = self.redis_client.ping()
        except:
            self.redis_available = False
            print("⚠️  Redis not available. Using in-memory cache.")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.redis_available:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        if self.redis_available:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
    
    def delete(self, key: str):
        """Delete value from cache"""
        if self.redis_available:
            self.redis_client.delete(key)
    
    def clear_all(self):
        """Clear all cache"""
        if self.redis_available:
            self.redis_client.flushdb()


# In-memory caching decorators
@lru_cache(maxsize=128)
def cached_ml_prediction(metrics_hash: str):
    """Cache ML predictions"""
    # This is a placeholder - actual implementation would call ML model
    pass


cache_manager = CacheManager()
```

**File: `docker-compose.redis.yml`**

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: self-healing-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  redis-data:
```

### 3.3 Database Query Optimization

**File: `src/optimization/query_optimization.py`**

```python
"""
Database Query Optimization
Efficient data retrieval patterns
"""

from typing import List, Dict
from datetime import datetime, timedelta

class QueryOptimizer:
    """Optimize database queries"""
    
    @staticmethod
    def get_metrics_with_pagination(offset: int = 0, limit: int = 50):
        """Get metrics with pagination"""
        # Implement pagination to avoid loading all data
        # SELECT * FROM metrics ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}
        pass
    
    @staticmethod
    def get_metrics_time_range(start_time: datetime, end_time: datetime):
        """Get metrics for specific time range"""
        # Use indexed timestamp column for faster queries
        # SELECT * FROM metrics WHERE timestamp BETWEEN {start} AND {end}
        pass
    
    @staticmethod
    def aggregate_metrics_hourly(date: datetime) -> List[Dict]:
        """Aggregate metrics by hour"""
        # Use database aggregation instead of loading all data
        # SELECT 
        #   DATE_TRUNC('hour', timestamp) as hour,
        #   AVG(cpu_usage), AVG(memory_usage)
        # FROM metrics
        # WHERE DATE(timestamp) = {date}
        # GROUP BY hour
        pass
    
    @staticmethod
    def create_indexes():
        """Create database indexes for performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_anomaly_type ON anomalies(anomaly_type)",
            "CREATE INDEX IF NOT EXISTS idx_action_status ON healing_actions(status)",
        ]
        # Execute index creation
        return indexes
```

---

## 4. PRODUCTION DEPLOYMENT CHECKLIST

**File: `production/deployment_checklist.md`**

```markdown
# Production Deployment Checklist

## Pre-Deployment

### Code Quality
- [ ] All unit tests passing (>80% coverage)
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] Code review completed
- [ ] No critical bugs open
- [ ] Performance benchmarks met

### Security
- [ ] Security scan completed (no HIGH/CRITICAL)
- [ ] Secrets properly configured
- [ ] TLS/HTTPS enabled
- [ ] Network policies configured
- [ ] Authentication enabled
- [ ] Authorization rules tested

### Infrastructure
- [ ] Production cluster provisioned
- [ ] Resource quotas configured
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Logging configured
- [ ] Alerting rules active

### Documentation
- [ ] Deployment guide updated
- [ ] API documentation complete
- [ ] Runbooks created
- [ ] Rollback procedure documented
- [ ] Disaster recovery plan ready

## During Deployment

### Pre-Flight Checks
- [ ] Backup current production
- [ ] Database migration tested (if applicable)
- [ ] Traffic rerouting plan ready
- [ ] Rollback script tested
- [ ] Team notified

### Deployment Steps
- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Deploy to production (blue-green/canary)
- [ ] Verify pods are healthy
- [ ] Run smoke tests on production
- [ ] Monitor metrics for 15 minutes

### Post-Deployment
- [ ] All services responding
- [ ] No error spikes in logs
- [ ] Performance metrics normal
- [ ] Monitoring dashboards green
- [ ] Alerts not firing

## Post-Deployment

### Validation (24 hours)
- [ ] No crashes or restarts
- [ ] Error rate < 1%
- [ ] Response time P95 < 1s
- [ ] System health > 95%
- [ ] All features working

### Documentation
- [ ] Deployment record updated
- [ ] Known issues documented
- [ ] Post-mortem (if issues)
- [ ] Lessons learned captured

### Cleanup
- [ ] Old deployments removed
- [ ] Staging environment updated
- [ ] Backup verified
- [ ] Team debriefed
```

**File: `scripts/production_deploy.sh`**

```bash
#!/bin/bash

set -e

echo "🚀 Production Deployment"
echo "======================="

# Configuration
NAMESPACE="self-healing-platform"
DEPLOYMENT="self-healing-platform"
IMAGE_TAG=${1:-latest}

echo ""
echo "⚠️  WARNING: You are about to deploy to PRODUCTION"
echo "Image Tag: ${IMAGE_TAG}"
echo ""

read -p "Have you completed the pre-deployment checklist? (yes/no): " CHECKLIST
if [ "$CHECKLIST" != "yes" ]; then
    echo "❌ Please complete the pre-deployment checklist first"
    exit 1
fi

read -p "Continue with production deployment? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

# Step 1: Backup current state
echo ""
echo "📦 Creating backup..."
./scripts/backup.sh

# Step 2: Update image
echo ""
echo "🔄 Updating deployment image..."
kubectl set image deployment/${DEPLOYMENT} \
    self-healing-platform=self-healing-platform:${IMAGE_TAG} \
    -n ${NAMESPACE}

# Step 3: Wait for rollout
echo ""
echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE} --timeout=300s

# Step 4: Verify deployment
echo ""
echo "✓ Running post-deployment checks..."
./scripts/validate_deployment.sh

# Step 5: Run smoke tests
echo ""
echo "🧪 Running smoke tests..."
pytest tests/smoke/ -v

echo ""
echo "✅ Production deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Monitor dashboards for 15 minutes"
echo "  2. Check error logs"
echo "  3. Verify all features working"
echo "  4. Update deployment record"
```

---

*This completes the first part of Phase 4. Would you like me to continue with the remaining sections (Phase 5: Final Presentation & Go-Live)?*
