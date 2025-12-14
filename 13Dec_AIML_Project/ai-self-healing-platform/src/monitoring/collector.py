"""
Observability & Metrics Collection Service
Collects metrics, logs, and traces from cloud workloads
"""

import asyncio
import psutil
import time
import logging
from datetime import datetime
from typing import Dict, List
import json
from dataclasses import dataclass, asdict
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System-level metrics"""
    timestamp: str
    cpu_usage: float
    cpu_per_core: List[float]
    memory_usage: float
    memory_available_mb: float
    disk_usage: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_bytes_sent: float
    network_bytes_recv: float
    
@dataclass
class ApplicationMetrics:
    """Application-level metrics"""
    timestamp: str
    requests_per_sec: float
    response_time_avg: float
    response_time_p95: float
    response_time_p99: float
    error_rate: float
    active_connections: int
    queue_depth: int
    
@dataclass
class TraceSpan:
    """Distributed trace span"""
    trace_id: str
    span_id: str
    parent_span_id: str
    service_name: str
    operation_name: str
    start_time: str
    duration_ms: float
    status: str
    tags: Dict

class MetricsCollector:
    """Collects system and application metrics"""
    
    def __init__(self, collection_interval: int = 5):
        self.collection_interval = collection_interval
        self.metrics_buffer = []
        self.last_network = psutil.net_io_counters()
        self.last_disk = psutil.disk_io_counters()
        self.last_time = time.time()
        
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics using psutil"""
        try:
            current_time = time.time()
            time_delta = current_time - self.last_time
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            disk_read_rate = (disk_io.read_bytes - self.last_disk.read_bytes) / time_delta / (1024 * 1024)
            disk_write_rate = (disk_io.write_bytes - self.last_disk.write_bytes) / time_delta / (1024 * 1024)
            
            # Network metrics
            network = psutil.net_io_counters()
            network_sent_rate = (network.bytes_sent - self.last_network.bytes_sent) / time_delta / 1024
            network_recv_rate = (network.bytes_recv - self.last_network.bytes_recv) / time_delta / 1024
            
            # Update last values
            self.last_network = network
            self.last_disk = disk_io
            self.last_time = current_time
            
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_usage=cpu_percent,
                cpu_per_core=cpu_per_core,
                memory_usage=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage=disk.percent,
                disk_io_read_mb=disk_read_rate,
                disk_io_write_mb=disk_write_rate,
                network_bytes_sent=network_sent_rate,
                network_bytes_recv=network_recv_rate
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            return None
    
    def simulate_application_metrics(self) -> ApplicationMetrics:
        """
        Simulate application metrics
        In production, these would come from:
        - Prometheus exporters
        - APM agents (New Relic, Datadog, etc.)
        - Custom instrumentation
        """
        # Simulate realistic patterns with occasional spikes
        base_rps = 100
        base_response = 200
        
        # Add variability
        rps = base_rps + random.uniform(-20, 30)
        response_avg = base_response + random.uniform(-50, 100)
        
        # Occasional spikes (10% chance)
        if random.random() < 0.1:
            response_avg *= 1.5
            rps *= 0.8
        
        metrics = ApplicationMetrics(
            timestamp=datetime.now().isoformat(),
            requests_per_sec=max(0, rps),
            response_time_avg=max(50, response_avg),
            response_time_p95=response_avg * 1.5,
            response_time_p99=response_avg * 2.0,
            error_rate=max(0, random.uniform(0, 2)),
            active_connections=random.randint(50, 200),
            queue_depth=random.randint(0, 50)
        )
        
        return metrics
    
    async def start_collection(self, callback=None):
        """Start continuous metrics collection"""
        logger.info("Starting metrics collection...")
        
        while True:
            try:
                system_metrics = await self.collect_system_metrics()
                app_metrics = self.simulate_application_metrics()
                
                combined_metrics = {
                    'system': asdict(system_metrics) if system_metrics else {},
                    'application': asdict(app_metrics),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.metrics_buffer.append(combined_metrics)
                
                # Keep buffer size manageable
                if len(self.metrics_buffer) > 1000:
                    self.metrics_buffer = self.metrics_buffer[-1000:]
                
                # Callback for real-time processing
                if callback:
                    await callback(combined_metrics)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in collection loop: {str(e)}")
                await asyncio.sleep(self.collection_interval)


class LogAggregator:
    """Aggregate and analyze logs"""
    
    def __init__(self):
        self.log_buffer = []
        self.error_patterns = []
        
    def ingest_log(self, log_entry: Dict):
        """Ingest a log entry"""
        self.log_buffer.append({
            **log_entry,
            'ingested_at': datetime.now().isoformat()
        })
        
        # Detect error patterns
        if log_entry.get('level') in ['ERROR', 'CRITICAL']:
            self._analyze_error(log_entry)
        
        # Keep buffer manageable
        if len(self.log_buffer) > 10000:
            self.log_buffer = self.log_buffer[-10000:]
    
    def _analyze_error(self, log_entry: Dict):
        """Analyze error logs for patterns"""
        message = log_entry.get('message', '')
        
        # Simple pattern matching (in production, use NLP)
        patterns = {
            'database': ['connection refused', 'timeout', 'deadlock'],
            'memory': ['out of memory', 'heap space', 'memory leak'],
            'network': ['connection reset', 'network unreachable', 'timeout']
        }
        
        for category, keywords in patterns.items():
            if any(keyword in message.lower() for keyword in keywords):
                self.error_patterns.append({
                    'category': category,
                    'message': message,
                    'timestamp': log_entry.get('timestamp'),
                    'severity': log_entry.get('level')
                })
    
    def get_error_summary(self, last_minutes: int = 5) -> Dict:
        """Get summary of recent errors"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(minutes=last_minutes)
        
        recent_errors = [
            log for log in self.log_buffer
            if log.get('level') in ['ERROR', 'CRITICAL']
            and datetime.fromisoformat(log['timestamp']) > cutoff
        ]
        
        return {
            'total_errors': len(recent_errors),
            'error_rate': len(recent_errors) / last_minutes,
            'patterns': self.error_patterns[-10:],
            'sample_errors': recent_errors[:5]
        }


class DistributedTracer:
    """Simple distributed tracing implementation"""
    
    def __init__(self):
        self.traces = {}
        
    def create_trace(self, service_name: str, operation: str) -> TraceSpan:
        """Create a new trace span"""
        import uuid
        
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id="",
            service_name=service_name,
            operation_name=operation,
            start_time=datetime.now().isoformat(),
            duration_ms=0,
            status="started",
            tags={}
        )
        
        self.traces[trace_id] = [span]
        return span
    
    def add_child_span(self, parent_span: TraceSpan, service_name: str, 
                       operation: str) -> TraceSpan:
        """Add a child span to existing trace"""
        import uuid
        
        span = TraceSpan(
            trace_id=parent_span.trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span.span_id,
            service_name=service_name,
            operation_name=operation,
            start_time=datetime.now().isoformat(),
            duration_ms=0,
            status="started",
            tags={}
        )
        
        self.traces[parent_span.trace_id].append(span)
        return span
    
    def finish_span(self, span: TraceSpan, status: str = "success", 
                    tags: Dict = None):
        """Finish a span"""
        start = datetime.fromisoformat(span.start_time)
        duration = (datetime.now() - start).total_seconds() * 1000
        
        span.duration_ms = duration
        span.status = status
        if tags:
            span.tags.update(tags)
    
    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a trace"""
        return self.traces.get(trace_id, [])
    
    def analyze_slow_traces(self, threshold_ms: float = 1000) -> List[Dict]:
        """Find slow traces"""
        slow_traces = []
        
        for trace_id, spans in self.traces.items():
            total_duration = sum(span.duration_ms for span in spans)
            if total_duration > threshold_ms:
                slow_traces.append({
                    'trace_id': trace_id,
                    'total_duration_ms': total_duration,
                    'spans': [asdict(span) for span in spans],
                    'bottleneck': max(spans, key=lambda s: s.duration_ms).operation_name
                })
        
        return slow_traces


# Example usage
if __name__ == '__main__':
    async def process_metrics(metrics):
        """Callback to process collected metrics"""
        logger.info(f"CPU: {metrics['system']['cpu_usage']:.1f}% | "
                   f"Memory: {metrics['system']['memory_usage']:.1f}% | "
                   f"RPS: {metrics['application']['requests_per_sec']:.0f}")
    
    async def main():
        collector = MetricsCollector(collection_interval=2)
        log_aggregator = LogAggregator()
        tracer = DistributedTracer()
        
        # Start metrics collection
        collection_task = asyncio.create_task(
            collector.start_collection(callback=process_metrics)
        )
        
        # Simulate some log entries
        for i in range(5):
            log_aggregator.ingest_log({
                'level': 'ERROR' if i % 3 == 0 else 'INFO',
                'message': 'Database connection timeout' if i % 3 == 0 else 'Request processed',
                'timestamp': datetime.now().isoformat(),
                'service': 'api-gateway'
            })
        
        # Simulate a traced request
        root_span = tracer.create_trace('api-gateway', 'GET /users')
        await asyncio.sleep(0.1)
        
        db_span = tracer.add_child_span(root_span, 'database', 'SELECT users')
        await asyncio.sleep(0.05)
        tracer.finish_span(db_span, 'success', {'rows': 150})
        
        tracer.finish_span(root_span, 'success', {'status_code': 200})
        
        # Get error summary
        error_summary = log_aggregator.get_error_summary(last_minutes=1)
        logger.info(f"Error summary: {json.dumps(error_summary, indent=2)}")
        
        # Run for 10 seconds then stop
        await asyncio.sleep(10)
        collection_task.cancel()
    
    asyncio.run(main())
    