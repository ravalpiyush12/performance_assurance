# Gunicorn Configuration for Oracle SQL API
import multiprocessing
import sys

# Server Socket
bind = "0.0.0.0:8000"

# Worker Processes
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"

# Preload app for better multi-database handling
preload_app = True

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
capture_output = True

# Timeouts
timeout = 300
graceful_timeout = 30
keepalive = 5

# Process naming
proc_name = "oracle-sql-api"

# Log configuration
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'default',
        },
        'error_console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'formatter': 'default',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'error_console'],
    },
}

# Startup message
print("=" * 70, file=sys.stdout, flush=True)
print("Gunicorn Configuration Loaded", file=sys.stdout, flush=True)
print(f"Workers: {workers}", file=sys.stdout, flush=True)
print(f"Bind: {bind}", file=sys.stdout, flush=True)
print(f"Preload App: {preload_app}", file=sys.stdout, flush=True)
print("=" * 70, file=sys.stdout, flush=True)
sys.stdout.flush()