from flask import Flask, jsonify, request
import time, random, hashlib, os, psutil, threading
from prometheus_client import Counter, Histogram, Gauge, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)
process = psutil.Process(os.getpid())

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
CPU_USAGE = Gauge('app_cpu_usage_percent', 'CPU usage')
MEMORY_USAGE = Gauge('app_memory_usage_bytes', 'Memory usage')

# CPU monitor thread
def monitor_cpu():
    process.cpu_percent()  # Initialize
    while True:
        cpu = process.cpu_percent(interval=1)
        CPU_USAGE.set(cpu)
        mem = process.memory_info().rss
        MEMORY_USAGE.set(mem)
        print(f"[METRICS] CPU: {cpu}% Memory: {mem/1024/1024:.1f}MB")

threading.Thread(target=monitor_cpu, daemon=True).start()

@app.after_request
def track(response):
    REQUEST_COUNT.labels(request.method, request.endpoint or 'unknown', response.status_code).inc()
    return response

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/compute')
def compute():
    result = 0
    for i in range(random.randint(100000, 500000)):
        result += len(hashlib.sha256(f"compute_{i}".encode()).hexdigest())
    return jsonify({'status': 'success', 'result': result})

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/metrics': make_wsgi_app()})

if __name__ == '__main__':
    print(f"Starting on port 5000")
    app.run(host='0.0.0.0', port=5000)