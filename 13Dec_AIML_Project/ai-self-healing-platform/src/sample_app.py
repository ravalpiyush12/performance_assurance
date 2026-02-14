"""
Sample Application with Prometheus Metrics (UPDATED)
This version properly exposes metrics for Prometheus to scrape

Features:
- /metrics endpoint (Prometheus format)
- Automatic instrumentation (request count, duration, etc.)
- Custom metrics (CPU, memory usage)

Deploy this as the target application for monitoring
"""

from flask import Flask, jsonify, request
import time
import random
import hashlib
import os
import psutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app

app = Flask(__name__)

# ==============================================================================
# PROMETHEUS METRICS DEFINITIONS
# ==============================================================================

# HTTP Request metrics (automatic)
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Custom application metrics
CPU_USAGE = Gauge('app_cpu_usage_percent', 'Current CPU usage percentage')
MEMORY_USAGE = Gauge('app_memory_usage_bytes', 'Current memory usage in bytes')
MEMORY_PERCENT = Gauge('app_memory_usage_percent', 'Current memory usage percentage')
ACTIVE_REQUESTS = Gauge('app_active_requests', 'Number of active requests')
ERROR_COUNT = Counter('app_errors_total', 'Total number of errors', ['endpoint', 'error_type'])

# Global storage for memory stress
memory_hog = []

# ==============================================================================
# PROMETHEUS MIDDLEWARE
# ==============================================================================

@app.before_request
def before_request():
    """Track request start time and increment active requests"""
    request.start_time = time.time()
    ACTIVE_REQUESTS.inc()
    
    # Update system metrics
    process = psutil.Process(os.getpid())
    CPU_USAGE.set(process.cpu_percent())
    mem_info = process.memory_info()
    MEMORY_USAGE.set(mem_info.rss)
    MEMORY_PERCENT.set(process.memory_percent())

@app.after_request
def after_request(response):
    """Track request duration and count"""
    ACTIVE_REQUESTS.dec()
    
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(duration)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()
    
    return response

# ==============================================================================
# APPLICATION ENDPOINTS
# ==============================================================================

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app': 'sample-application',
        'version': '1.0',
        'metrics_endpoint': '/metrics'
    })

@app.route('/compute')
def compute_intensive():
    """
    CPU intensive endpoint
    Creates REAL CPU load when hit by JMeter
    """
    try:
        iterations = random.randint(100000, 500000)
        result = 0
        
        for i in range(iterations):
            data = f"compute_{i}".encode()
            hash_result = hashlib.sha256(data).hexdigest()
            result += len(hash_result)
        
        # Update CPU metric
        process = psutil.Process(os.getpid())
        CPU_USAGE.set(process.cpu_percent())
        
        return jsonify({
            'status': 'success',
            'iterations': iterations,
            'result_length': result,
            'message': 'CPU intensive task completed',
            'cpu_usage': process.cpu_percent()
        })
    except Exception as e:
        ERROR_COUNT.labels(endpoint='compute', error_type=type(e).__name__).inc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/memory')
def memory_intensive():
    """
    Memory intensive endpoint
    Creates REAL memory load
    """
    global memory_hog
    
    try:
        # Allocate 10MB
        chunk_size = 10 * 1024 * 1024
        data = 'x' * chunk_size
        memory_hog.append(data)
        
        # Keep only last 5 chunks (50MB max)
        if len(memory_hog) > 5:
            memory_hog.pop(0)
        
        # Update memory metric
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        MEMORY_USAGE.set(mem_info.rss)
        MEMORY_PERCENT.set(process.memory_percent())
        
        return jsonify({
            'status': 'success',
            'memory_allocated_mb': len(memory_hog) * 10,
            'memory_usage_mb': mem_info.rss / (1024 * 1024),
            'message': 'Memory intensive task completed'
        })
    except Exception as e:
        ERROR_COUNT.labels(endpoint='memory', error_type=type(e).__name__).inc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/slow')
def slow_response():
    """Simulates slow response time"""
    try:
        delay = random.uniform(1.0, 5.0)
        time.sleep(delay)
        
        return jsonify({
            'status': 'success',
            'delay_seconds': round(delay, 2),
            'message': 'Slow response simulated'
        })
    except Exception as e:
        ERROR_COUNT.labels(endpoint='slow', error_type=type(e).__name__).inc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/data', methods=['POST'])
def database_operation():
    """Simulates database operations"""
    try:
        data = request.get_json() or {}
        time.sleep(random.uniform(0.1, 0.5))
        
        for i in range(10000):
            _ = hashlib.md5(f"{i}_{data}".encode()).hexdigest()
        
        return jsonify({
            'status': 'success',
            'processed': True,
            'message': 'Database operation completed'
        })
    except Exception as e:
        ERROR_COUNT.labels(endpoint='data', error_type=type(e).__name__).inc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/error')
def simulate_error():
    """Randomly returns errors"""
    try:
        if random.random() < 0.3:
            ERROR_COUNT.labels(endpoint='error', error_type='SimulatedError').inc()
            return jsonify({
                'status': 'error',
                'message': 'Simulated error occurred'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Request successful'
        })
    except Exception as e:
        ERROR_COUNT.labels(endpoint='error', error_type=type(e).__name__).inc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/cleanup')
def cleanup():
    """Clear memory hog"""
    global memory_hog
    memory_hog.clear()
    
    # Update metrics
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    MEMORY_USAGE.set(mem_info.rss)
    MEMORY_PERCENT.set(process.memory_percent())
    
    return jsonify({
        'status': 'success',
        'message': 'Memory cleared',
        'memory_usage_mb': mem_info.rss / (1024 * 1024)
    })

# ==============================================================================
# PROMETHEUS METRICS ENDPOINT
# ==============================================================================

# Add Prometheus metrics endpoint
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Sample Application on port {port}")
    print(f"Metrics available at: http://localhost:{port}/metrics")
    print(f"Health check at: http://localhost:{port}/health")
    app.run(host='0.0.0.0', port=port, debug=False)