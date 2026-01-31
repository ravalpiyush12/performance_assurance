"""
Shared pytest fixtures and configuration
File: tests/conftest.py
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create temporary directory for test data"""
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture
def sample_metric():
    """Generate sample metric data"""
    return {
        'timestamp': datetime.now().isoformat(),
        'cpu_usage': 50.0,
        'memory_usage': 60.0,
        'response_time': 200.0,
        'error_rate': 1.0,
        'requests_per_sec': 100.0,
        'disk_io': 1000.0,
        'network_throughput': 500.0
    }


@pytest.fixture
def sample_metrics_batch():
    """Generate batch of sample metrics"""
    import numpy as np
    
    metrics = []
    for i in range(20):
        metric = {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': 50 + np.random.randn() * 5,
            'memory_usage': 60 + np.random.randn() * 5,
            'response_time': 200 + np.random.randn() * 20,
            'error_rate': 0.5 + np.random.randn() * 0.2,
            'requests_per_sec': 100 + np.random.randn() * 10,
            'disk_io': 1000 + np.random.randn() * 100,
            'network_throughput': 500 + np.random.randn() * 50
        }
        metrics.append(metric)
    
    return metrics


@pytest.fixture
def anomalous_metric():
    """Generate anomalous metric data"""
    return {
        'timestamp': datetime.now().isoformat(),
        'cpu_usage': 95.0,
        'memory_usage': 90.0,
        'response_time': 1500.0,
        'error_rate': 10.0,
        'requests_per_sec': 20.0,
        'disk_io': 5000.0,
        'network_throughput': 2000.0
    }


@pytest.fixture
def cpu_anomaly():
    """CPU usage anomaly"""
    return {
        'anomaly_type': 'CPU_USAGE',
        'severity': 'warning',
        'metrics': {
            'cpu_usage': 85,
            'memory_usage': 70,
            'response_time': 300
        }
    }


@pytest.fixture
def memory_anomaly():
    """Memory usage anomaly"""
    return {
        'anomaly_type': 'MEMORY_USAGE',
        'severity': 'warning',
        'metrics': {
            'cpu_usage': 60,
            'memory_usage': 90,
            'response_time': 300
        }
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after each test"""
    yield
    # Add any cleanup code here


# Logging configuration for tests
@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for tests"""
    import logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise in tests
        format='%(levelname)s - %(message)s'
    )