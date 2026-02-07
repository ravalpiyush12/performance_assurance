"""
Monitoring Module - System and Application Metrics Collection
Collects system resources and application performance metrics
"""

import psutil
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import deque
import asyncio
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApplicationMetricsCollector:
    """
    Collects application-level metrics (requests, errors, response times)
    """
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=1000)
        self.start_time = datetime.now()
        logger.info("ApplicationMetricsCollector initialized")
    
    def increment_request_count(self):
        """Increment total request count"""
        self.request_count += 1
    
    def increment_error_count(self):
        """Increment error count"""
        self.error_count += 1
    
    def record_response_time(self, response_time: float):
        """Record a response time"""
        self.response_times.append(response_time)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get application metrics summary"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate statistics
        response_times_list = list(self.response_times)
        avg_response_time = statistics.mean(response_times_list) if response_times_list else 0
        
        # Calculate percentiles
        p95 = 0
        if len(response_times_list) >= 20:
            sorted_times = sorted(response_times_list)
            p95_index = int(len(sorted_times) * 0.95)
            p95 = sorted_times[p95_index]
        
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            "uptime_seconds": round(uptime, 2),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": round(error_rate, 2),
            "avg_response_time": round(avg_response_time, 3),
            "p95_response_time": round(p95, 3),
            "requests_per_second": round(self.request_count / uptime, 2) if uptime > 0 else 0
        }


class MetricsCollector:
    """
    Collects system metrics asynchronously
    """
    
    def __init__(self, collection_interval: int = 5):
        """
        Initialize metrics collector
        
        Args:
            collection_interval: Seconds between collections
        """
        self.collection_interval = collection_interval
        self.metrics_history = deque(maxlen=1000)
        self.is_collecting = False
        logger.info(f"MetricsCollector initialized (interval: {collection_interval}s)")
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            net_io = psutil.net_io_counters()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                # CPU
                'cpu_usage': round(cpu_percent, 2),
                'cpu_count': cpu_count,
                'cpu_freq_mhz': round(cpu_freq.current, 2) if cpu_freq else 0,
                # Memory
                'memory_usage': round(memory.percent, 2),
                'memory_available_mb': round(memory.available / 1024 / 1024, 2),
                'memory_total_mb': round(memory.total / 1024 / 1024, 2),
                # Disk
                'disk_usage': round(disk.percent, 2),
                'disk_free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                'disk_total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
                'disk_read_mb': round(disk_io.read_bytes / 1024 / 1024, 2) if disk_io else 0,
                'disk_write_mb': round(disk_io.write_bytes / 1024 / 1024, 2) if disk_io else 0,
                # Network
                'network_sent_mb': round(net_io.bytes_sent / 1024 / 1024, 2),
                'network_recv_mb': round(net_io.bytes_recv / 1024 / 1024, 2)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    async def start_collection(self):
        """Start collecting metrics in background"""
        if self.is_collecting:
            logger.warning("Metrics collection already running")
            return
        
        self.is_collecting = True
        logger.info("Started system metrics collection")
        
        while self.is_collecting:
            try:
                metrics = self.collect_system_metrics()
                if metrics:
                    self.metrics_history.append(metrics)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def stop_collection(self):
        """Stop collecting metrics"""
        self.is_collecting = False
        logger.info("Stopped system metrics collection")
    
    def get_recent_metrics(self, limit: int = 10) -> List[Dict]:
        """Get recent metrics"""
        return list(self.metrics_history)[-limit:]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary statistics of collected metrics"""
        if not self.metrics_history:
            return {"message": "No metrics collected yet"}
        
        metrics_list = list(self.metrics_history)
        
        # Calculate averages
        avg_cpu = statistics.mean([m.get('cpu_usage', 0) for m in metrics_list])
        avg_memory = statistics.mean([m.get('memory_usage', 0) for m in metrics_list])
        avg_disk = statistics.mean([m.get('disk_usage', 0) for m in metrics_list])
        
        # Get latest values
        latest = metrics_list[-1] if metrics_list else {}
        
        return {
            'total_samples': len(metrics_list),
            'latest': latest,
            'averages': {
                'cpu_usage': round(avg_cpu, 2),
                'memory_usage': round(avg_memory, 2),
                'disk_usage': round(avg_disk, 2)
            },
            'timestamp': datetime.now().isoformat()
        }


# Example usage
if __name__ == '__main__':
    import asyncio
    
    async def test_collector():
        collector = MetricsCollector(collection_interval=2)
        
        # Start collection
        task = asyncio.create_task(collector.start_collection())
        
        # Wait for some metrics
        await asyncio.sleep(10)
        
        # Get summary
        summary = collector.get_metrics_summary()
        print("\nMetrics Summary:")
        print(f"Samples collected: {summary['total_samples']}")
        print(f"Average CPU: {summary['averages']['cpu_usage']}%")
        print(f"Average Memory: {summary['averages']['memory_usage']}%")
        
        # Stop collection
        collector.stop_collection()
        await task
    
    # Run test
    asyncio.run(test_collector())