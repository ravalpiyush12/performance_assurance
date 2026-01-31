"""
Production vs PTE Traffic Analysis System with Oracle Database Integration
Compares real-time production traffic against certification volumes,
identifies discrepancies, validates testing efficacy, and defines critical metrics.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from scipy import stats
from collections import defaultdict
import json
import cx_Oracle
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrafficMetrics:
    """Core traffic metrics for comparison"""
    timestamp: datetime
    request_rate: float
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    error_rate: float
    throughput: float
    concurrent_users: int
    cpu_utilization: float
    memory_utilization: float
    db_connections: int
    cache_hit_rate: float


@dataclass
class DiscrepancyReport:
    """Discrepancy findings between prod and PTE"""
    metric_name: str
    prod_value: float
    pte_value: float
    discrepancy_pct: float
    severity: str
    recommendation: str


class OracleDBConnector:
    """Oracle Database connection manager"""
    
    def __init__(self, username: str, password: str, dsn: str):
        self.username = username
        self.password = password
        self.dsn = dsn
        self.connection = None
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = cx_Oracle.connect(
                user=self.username,
                password=self.password,
                dsn=self.dsn,
                encoding="UTF-8"
            )
            yield conn
        except cx_Oracle.Error as e:
            logger.error(f"Oracle connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def fetch_prod_traffic(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Fetch production traffic data from Oracle"""
        query = """
        SELECT 
            metric_timestamp,
            request_rate,
            response_time_p50,
            response_time_p95,
            response_time_p99,
            error_rate,
            throughput_mbps,
            concurrent_users,
            cpu_utilization,
            memory_utilization,
            db_connections,
            cache_hit_rate,
            endpoint_name,
            http_method
        FROM prod_traffic_metrics
        WHERE metric_timestamp BETWEEN :start_time AND :end_time
        ORDER BY metric_timestamp
        """
        
        try:
            with self.get_connection() as conn:
                df = pd.read_sql(
                    query, 
                    conn, 
                    params={'start_time': start_time, 'end_time': end_time}
                )
            
            df['metric_timestamp'] = pd.to_datetime(df['metric_timestamp'])
            logger.info(f"Fetched {len(df)} production traffic records")
            return df
        except Exception as e:
            logger.error(f"Error fetching production traffic: {e}")
            return pd.DataFrame()
    
    def fetch_pte_traffic(self, test_run_id: Optional[str] = None) -> pd.DataFrame:
        """Fetch PTE certification test data from Oracle"""
        if test_run_id:
            query = """
            SELECT 
                t.metric_timestamp,
                t.request_rate,
                t.response_time_p50,
                t.response_time_p95,
                t.response_time_p99,
                t.error_rate,
                t.throughput_mbps,
                t.concurrent_users,
                t.cpu_utilization,
                t.memory_utilization,
                t.db_connections,
                t.cache_hit_rate,
                t.endpoint_name,
                t.http_method,
                r.test_type,
                r.load_pattern,
                r.test_duration_minutes,
                r.test_description
            FROM pte_traffic_metrics t
            JOIN pte_test_runs r ON t.test_run_id = r.test_run_id
            WHERE t.test_run_id = :test_run_id
            ORDER BY t.metric_timestamp
            """
            params = {'test_run_id': test_run_id}
        else:
            query = """
            SELECT 
                t.metric_timestamp,
                t.request_rate,
                t.response_time_p50,
                t.response_time_p95,
                t.response_time_p99,
                t.error_rate,
                t.throughput_mbps,
                t.concurrent_users,
                t.cpu_utilization,
                t.memory_utilization,
                t.db_connections,
                t.cache_hit_rate,
                t.endpoint_name,
                t.http_method,
                r.test_type,
                r.load_pattern,
                r.test_duration_minutes,
                r.test_description,
                r.test_run_id
            FROM pte_traffic_metrics t
            JOIN pte_test_runs r ON t.test_run_id = r.test_run_id
            WHERE r.test_status = 'COMPLETED'
            AND r.test_timestamp >= SYSDATE - 30
            ORDER BY t.metric_timestamp
            """
            params = {}
        
        try:
            with self.get_connection() as conn:
                df = pd.read_sql(query, conn, params=params)
            
            df['metric_timestamp'] = pd.to_datetime(df['metric_timestamp'])
            logger.info(f"Fetched {len(df)} PTE traffic records")
            return df
        except Exception as e:
            logger.error(f"Error fetching PTE traffic: {e}")
            return pd.DataFrame()
    
    def fetch_endpoint_coverage(self) -> pd.DataFrame:
        """Fetch endpoint coverage comparison"""
        query = """
        WITH prod_endpoints AS (
            SELECT DISTINCT endpoint_name, http_method
            FROM prod_traffic_metrics
            WHERE metric_timestamp >= SYSDATE - 7
        ),
        pte_endpoints AS (
            SELECT DISTINCT endpoint_name, http_method
            FROM pte_traffic_metrics
            WHERE test_run_id IN (
                SELECT test_run_id FROM pte_test_runs 
                WHERE test_status = 'COMPLETED' 
                AND test_timestamp >= SYSDATE - 30
            )
        )
        SELECT 
            p.endpoint_name,
            p.http_method,
            CASE WHEN t.endpoint_name IS NOT NULL THEN 'Y' ELSE 'N' END as tested_in_pte
        FROM prod_endpoints p
        LEFT JOIN pte_endpoints t 
            ON p.endpoint_name = t.endpoint_name 
            AND p.http_method = t.http_method
        ORDER BY tested_in_pte, p.endpoint_name
        """
        
        try:
            with self.get_connection() as conn:
                df = pd.read_sql(query, conn)
            logger.info(f"Fetched endpoint coverage for {len(df)} endpoints")
            return df
        except Exception as e:
            logger.error(f"Error fetching endpoint coverage: {e}")
            return pd.DataFrame()
    
    def save_discrepancy_report(self, report: DiscrepancyReport, analysis_id: str):
        """Save discrepancy findings to Oracle"""
        insert_query = """
        INSERT INTO discrepancy_reports (
            analysis_id, metric_name, prod_value, pte_value, 
            discrepancy_pct, severity, recommendation, created_date
        ) VALUES (
            :analysis_id, :metric_name, :prod_value, :pte_value,
            :discrepancy_pct, :severity, :recommendation, SYSDATE
        )
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_query, {
                    'analysis_id': analysis_id,
                    'metric_name': report.metric_name,
                    'prod_value': report.prod_value,
                    'pte_value': report.pte_value,
                    'discrepancy_pct': report.discrepancy_pct,
                    'severity': report.severity,
                    'recommendation': report.recommendation
                })
                conn.commit()
                logger.info(f"Saved discrepancy report for {report.metric_name}")
        except Exception as e:
            logger.error(f"Error saving discrepancy report: {e}")


class ProductionTrafficAnalyzer:
    """Analyzes production traffic patterns"""
    
    def __init__(self, db_connector: OracleDBConnector):
        self.db = db_connector
        self.baseline_metrics = None
    
    def calculate_baseline(self, window_hours: int = 24) -> Dict:
        """Calculate baseline from recent production data"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=window_hours)
        
        df = self.db.fetch_prod_traffic(start_time, end_time)
        
        if df.empty:
            logger.warning("No production data available for baseline calculation")
            return {}
        
        baseline = {
            'avg_request_rate': float(df['request_rate'].mean()),
            'peak_request_rate': float(df['request_rate'].max()),
            'min_request_rate': float(df['request_rate'].min()),
            'avg_response_time': float(df['response_time_p50'].mean()),
            'p95_response_time': float(df['response_time_p95'].quantile(0.95)),
            'p99_response_time': float(df['response_time_p99'].quantile(0.99)),
            'avg_error_rate': float(df['error_rate'].mean()),
            'max_error_rate': float(df['error_rate'].max()),
            'avg_throughput': float(df['throughput_mbps'].mean()),
            'peak_throughput': float(df['throughput_mbps'].max()),
            'avg_concurrent_users': float(df['concurrent_users'].mean()),
            'peak_concurrent_users': int(df['concurrent_users'].max()),
            'avg_cpu': float(df['cpu_utilization'].mean()),
            'peak_cpu': float(df['cpu_utilization'].max()),
            'avg_memory': float(df['memory_utilization'].mean()),
            'peak_memory': float(df['memory_utilization'].max()),
            'unique_endpoints': int(df['endpoint_name'].nunique()),
            'total_requests': len(df),
            'window_hours': window_hours,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        self.baseline_metrics = baseline
        logger.info(f"Calculated baseline with {baseline['total_requests']} samples")
        return baseline
    
    def detect_traffic_patterns(self, window_days: int = 7) -> Dict:
        """Identify traffic patterns from Oracle data"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        
        df = self.db.fetch_prod_traffic(start_time, end_time)
        
        if len(df) < 24:
            logger.warning("Insufficient data for pattern detection")
            return {'status': 'insufficient_data'}
        
        df['hour'] = df['metric_timestamp'].dt.hour
        df['day_of_week'] = df['metric_timestamp'].dt.dayofweek
        
        patterns = {
            'hourly_pattern': df.groupby('hour')['request_rate'].mean().to_dict(),
            'daily_pattern': df.groupby('day_of_week')['request_rate'].mean().to_dict(),
            'peak_hours': df.groupby('hour')['request_rate'].mean().nlargest(3).index.tolist(),
            'low_hours': df.groupby('hour')['request_rate'].mean().nsmallest(3).index.tolist(),
            'volatility': float(df['request_rate'].std() / df['request_rate'].mean()) if df['request_rate'].mean() > 0 else 0,
            'spike_events': self._detect_spikes(df),
            'endpoint_distribution': df.groupby('endpoint_name')['request_rate'].sum().to_dict()
        }
        
        logger.info(f"Detected {len(patterns['spike_events'])} spike events")
        return patterns
    
    def _detect_spikes(self, df: pd.DataFrame) -> List[Dict]:
        """Detect traffic spikes using statistical methods"""
        mean = df['request_rate'].mean()
        std = df['request_rate'].std()
        threshold = mean + 2 * std
        
        spikes = df[df['request_rate'] > threshold]
        return [{
            'timestamp': str(row['metric_timestamp']),
            'request_rate': float(row['request_rate']),
            'magnitude': float((row['request_rate'] - mean) / std) if std > 0 else 0
        } for _, row in spikes.head(10).iterrows()]
    
    def get_endpoint_metrics(self, endpoint_name: str, window_hours: int = 24) -> Dict:
        """Get specific endpoint metrics"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=window_hours)
        
        df = self.db.fetch_prod_traffic(start_time, end_time)
        endpoint_df = df[df['endpoint_name'] == endpoint_name]
        
        if endpoint_df.empty:
            logger.warning(f"No data found for endpoint: {endpoint_name}")
            return {}
        
        return {
            'avg_request_rate': float(endpoint_df['request_rate'].mean()),
            'peak_request_rate': float(endpoint_df['request_rate'].max()),
            'avg_response_time': float(endpoint_df['response_time_p50'].mean()),
            'p95_response_time': float(endpoint_df['response_time_p95'].max()),
            'error_rate': float(endpoint_df['error_rate'].mean()),
            'request_count': len(endpoint_df)
        }


class PTECertificationAnalyzer:
    """Analyzes PTE certification test results from Oracle"""
    
    def __init__(self, db_connector: OracleDBConnector):
        self.db = db_connector
    
    def calculate_test_metrics(self, test_run_id: Optional[str] = None) -> Dict:
        """Calculate aggregate test metrics from PTE"""
        df = self.db.fetch_pte_traffic(test_run_id)
        
        if df.empty:
            logger.warning("No PTE test data available")
            return {}
        
        metrics = {
            'max_request_rate_tested': float(df['request_rate'].max()),
            'avg_request_rate_tested': float(df['request_rate'].mean()),
            'avg_response_time': float(df['response_time_p50'].mean()),
            'p95_response_time': float(df['response_time_p95'].max()),
            'p99_response_time': float(df['response_time_p99'].max()),
            'max_error_rate': float(df['error_rate'].max()),
            'avg_error_rate': float(df['error_rate'].mean()),
            'max_throughput': float(df['throughput_mbps'].max()),
            'max_concurrent_users': int(df['concurrent_users'].max()),
            'peak_cpu': float(df['cpu_utilization'].max()),
            'peak_memory': float(df['memory_utilization'].max()),
            'unique_endpoints_tested': int(df['endpoint_name'].nunique()),
            'total_test_samples': len(df)
        }
        
        if 'test_duration_minutes' in df.columns:
            metrics['total_test_duration'] = float(df['test_duration_minutes'].sum())
        
        if 'load_pattern' in df.columns:
            metrics['load_patterns'] = df['load_pattern'].unique().tolist()
        
        logger.info(f"Calculated PTE metrics from {metrics['total_test_samples']} samples")
        return metrics
    
    def get_test_coverage_gaps(self) -> Dict:
        """Identify gaps in test coverage"""
        coverage_df = self.db.fetch_endpoint_coverage()
        
        if coverage_df.empty:
            logger.warning("No coverage data available")
            return {}
        
        untested = coverage_df[coverage_df['tested_in_pte'] == 'N']
        tested = coverage_df[coverage_df['tested_in_pte'] == 'Y']
        
        return {
            'total_prod_endpoints': len(coverage_df),
            'tested_endpoints': len(tested),
            'untested_endpoints': len(untested),
            'coverage_percentage': float((len(tested) / len(coverage_df) * 100)) if len(coverage_df) > 0 else 0,
            'untested_list': untested[['endpoint_name', 'http_method']].to_dict('records')
        }


class DiscrepancyDetector:
    """Detects and analyzes discrepancies between prod and PTE"""
    
    def __init__(self, db_connector: OracleDBConnector, threshold_pct: float = 20.0):
        self.db = db_connector
        self.threshold_pct = threshold_pct
        self.discrepancies = []
    
    def compare_metrics(self, prod_baseline: Dict, pte_metrics: Dict) -> List[DiscrepancyReport]:
        """Compare production baseline against PTE test metrics"""
        discrepancies = []
        
        # Key metrics to compare with severity levels
        comparisons = [
            ('Request Rate', 'peak_request_rate', 'max_request_rate_tested', 'critical', True),
            ('P95 Response Time', 'p95_response_time', 'p95_response_time', 'high', False),
            ('P99 Response Time', 'p99_response_time', 'p99_response_time', 'high', False),
            ('Error Rate', 'max_error_rate', 'max_error_rate', 'critical', False),
            ('Throughput', 'peak_throughput', 'max_throughput', 'high', True),
            ('Concurrent Users', 'peak_concurrent_users', 'max_concurrent_users', 'medium', True),
            ('CPU Utilization', 'peak_cpu', 'peak_cpu', 'high', False),
            ('Memory Utilization', 'peak_memory', 'peak_memory', 'high', False),
        ]
        
        for metric_name, prod_key, pte_key, base_severity, higher_is_better in comparisons:
            if prod_key not in prod_baseline or pte_key not in pte_metrics:
                continue
            
            prod_val = prod_baseline[prod_key]
            pte_val = pte_metrics[pte_key]
            
            if prod_val == 0:
                continue
            
            # Calculate discrepancy
            if higher_is_better:
                discrepancy_pct = ((prod_val - pte_val) / prod_val) * 100
            else:
                discrepancy_pct = ((pte_val - prod_val) / prod_val) * 100
            
            if abs(discrepancy_pct) > self.threshold_pct:
                severity = self._determine_severity(abs(discrepancy_pct), base_severity)
                recommendation = self._generate_recommendation(
                    metric_name, discrepancy_pct, prod_val, pte_val, higher_is_better
                )
                
                report = DiscrepancyReport(
                    metric_name=metric_name,
                    prod_value=prod_val,
                    pte_value=pte_val,
                    discrepancy_pct=discrepancy_pct,
                    severity=severity,
                    recommendation=recommendation
                )
                
                discrepancies.append(report)
        
        self.discrepancies = discrepancies
        logger.info(f"Detected {len(discrepancies)} discrepancies")
        return discrepancies
    
    def _determine_severity(self, discrepancy_pct: float, base_severity: str) -> str:
        """Determine severity based on discrepancy magnitude"""
        if discrepancy_pct > 50:
            return 'critical'
        elif discrepancy_pct > 30:
            return 'high' if base_severity != 'critical' else 'critical'
        elif discrepancy_pct > 20:
            return 'medium' if base_severity == 'low' else base_severity
        else:
            return 'low'
    
    def _generate_recommendation(self, metric_name: str, discrepancy_pct: float, 
                                 prod_val: float, pte_val: float, higher_is_better: bool) -> str:
        """Generate actionable recommendations"""
        if higher_is_better and discrepancy_pct > 0:
            return f"PTE testing did not reach production {metric_name} levels. " \
                   f"Increase test load from {pte_val:.2f} to at least {prod_val:.2f} " \
                   f"to validate system behavior under actual production conditions."
        elif not higher_is_better and discrepancy_pct > 0:
            return f"{metric_name} in production is better than PTE tests showed. " \
                   f"Investigate why PTE showed {pte_val:.2f} vs production {prod_val:.2f}. " \
                   f"Review test environment configuration and load patterns."
        elif higher_is_better and discrepancy_pct < 0:
            return f"PTE exceeded production {metric_name}. " \
                   f"Tests may be over-provisioned or production is under-utilized. " \
                   f"Validate test scenarios match production use cases."
        else:
            return f"{metric_name} shows production degradation. " \
                   f"Production {prod_val:.2f} is worse than PTE {pte_val:.2f}. " \
                   f"Investigate production environment issues immediately."
    
    def save_analysis_results(self, analysis_id: str):
        """Save all discrepancies to Oracle database"""
        for report in self.discrepancies:
            self.db.save_discrepancy_report(report, analysis_id)


class TestEfficacyValidator:
    """Validates testing efficacy and defines critical metrics"""
    
    def __init__(self, prod_analyzer: ProductionTrafficAnalyzer, 
                 pte_analyzer: PTECertificationAnalyzer):
        self.prod_analyzer = prod_analyzer
        self.pte_analyzer = pte_analyzer
    
    def calculate_test_efficacy_score(self) -> Dict:
        """Calculate overall test efficacy score"""
        coverage = self.pte_analyzer.get_test_coverage_gaps()
        
        prod_baseline = self.prod_analyzer.baseline_metrics
        pte_metrics = self.pte_analyzer.calculate_test_metrics()
        
        if not prod_baseline or not pte_metrics:
            return {'error': 'Insufficient data for efficacy calculation'}
        
        # Calculate individual scores
        coverage_score = coverage.get('coverage_percentage', 0)
        
        # Load coverage
        load_score = min(100, (pte_metrics.get('max_request_rate_tested', 0) / 
                              prod_baseline.get('peak_request_rate', 1)) * 100)
        
        # Performance validation
        perf_score = 100
        if pte_metrics.get('p95_response_time', 0) > prod_baseline.get('p95_response_time', float('inf')):
            perf_score -= 30
        if pte_metrics.get('p99_response_time', 0) > prod_baseline.get('p99_response_time', float('inf')):
            perf_score -= 20
        
        # Error rate validation
        error_score = 100
        if pte_metrics.get('max_error_rate', 0) > prod_baseline.get('max_error_rate', 0):
            error_score = max(0, 100 - (pte_metrics['max_error_rate'] - prod_baseline['max_error_rate']) * 10)
        
        # Overall efficacy score (weighted average)
        efficacy_score = (
            coverage_score * 0.3 +
            load_score * 0.3 +
            perf_score * 0.2 +
            error_score * 0.2
        )
        
        result = {
            'overall_efficacy_score': round(efficacy_score, 2),
            'coverage_score': round(coverage_score, 2),
            'load_coverage_score': round(load_score, 2),
            'performance_score': round(perf_score, 2),
            'error_validation_score': round(error_score, 2),
            'rating': self._get_rating(efficacy_score)
        }
        
        logger.info(f"Test efficacy score: {result['overall_efficacy_score']}% ({result['rating']})")
        return result
    
    def _get_rating(self, score: float) -> str:
        """Convert score to rating"""
        if score >= 90:
            return 'Excellent'
        elif score >= 75:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        elif score >= 40:
            return 'Poor'
        else:
            return 'Inadequate'
    
    def define_critical_test_metrics(self) -> Dict:
        """Define critical metrics for system resilience and performance"""
        prod_baseline = self.prod_analyzer.baseline_metrics
        
        if not prod_baseline:
            logger.warning("No baseline available for defining critical metrics")
            return {}
        
        critical_metrics = {
            'load_testing': {
                'target_request_rate': prod_baseline.get('peak_request_rate', 0) * 1.5,
                'sustained_duration_minutes': 60,
                'spike_test_multiplier': 2.0,
                'description': 'Load capacity with headroom for traffic spikes'
            },
            'performance_sla': {
                'max_p50_response_time_ms': prod_baseline.get('avg_response_time', 0) * 1.2,
                'max_p95_response_time_ms': prod_baseline.get('p95_response_time', 0) * 1.3,
                'max_p99_response_time_ms': prod_baseline.get('p99_response_time', 0) * 1.5,
                'description': 'Response time thresholds under load'
            },
            'reliability': {
                'max_error_rate_pct': max(0.1, prod_baseline.get('avg_error_rate', 0)),
                'max_timeout_rate_pct': 0.05,
                'required_uptime_pct': 99.9,
                'description': 'Error rates and availability requirements'
            },
            'resource_limits': {
                'max_cpu_utilization_pct': 80,
                'max_memory_utilization_pct': 85,
                'max_db_connections': prod_baseline.get('peak_concurrent_users', 100) * 2,
                'description': 'Resource utilization safety thresholds'
            },
            'scalability': {
                'concurrent_users': prod_baseline.get('peak_concurrent_users', 0) * 1.5,
                'throughput_mbps': prod_baseline.get('peak_throughput', 0) * 1.5,
                'description': 'Scalability targets for growth'
            },
            'resilience': {
                'recovery_time_seconds': 30,
                'failover_time_seconds': 10,
                'data_loss_tolerance': 'zero',
                'description': 'Disaster recovery and failover requirements'
            }
        }
        
        logger.info("Defined critical test metrics based on production baseline")
        return critical_metrics


def run_comprehensive_analysis(db_config: Dict, test_run_id: Optional[str] = None) -> Dict:
    """
    Main function to run comprehensive prod vs PTE analysis
    
    Args:
        db_config: Dictionary with Oracle DB credentials
        test_run_id: Optional specific test run to analyze
    
    Returns:
        Complete analysis report
    """
    logger.info("Starting comprehensive production vs PTE analysis")
    
    # Initialize Oracle connector
    db = OracleDBConnector(
        username=db_config['username'],
        password=db_config['password'],
        dsn=db_config['dsn']
    )
    
    # Initialize analyzers
    prod_analyzer = ProductionTrafficAnalyzer(db)
    pte_analyzer = PTECertificationAnalyzer(db)
    discrepancy_detector = DiscrepancyDetector(db, threshold_pct=15.0)
    efficacy_validator = TestEfficacyValidator(prod_analyzer, pte_analyzer)
    
    # Step 1: Analyze production baseline
    logger.info("Step 1: Analyzing production traffic baseline...")
    prod_baseline = prod_analyzer.calculate_baseline(window_hours=24)
    prod_patterns = prod_analyzer.detect_traffic_patterns(window_days=7)
    
    # Step 2: Analyze PTE test results
    logger.info("Step 2: Analyzing PTE certification test results...")
    pte_metrics = pte_analyzer.calculate_test_metrics(test_run_id)
    coverage_gaps = pte_analyzer.get_test_coverage_gaps()
    
    # Step 3: Detect discrepancies
    logger.info("Step 3: Detecting discrepancies...")
    discrepancies = discrepancy_detector.compare_metrics(prod_baseline, pte_metrics)
    
    # Step 4: Calculate test efficacy
    logger.info("Step 4: Calculating test efficacy...")
    efficacy_score = efficacy_validator.calculate_test_efficacy_score()
    
    # Step 5: Define critical metrics
    logger.info("Step 5: Defining critical test metrics...")
    critical_metrics = efficacy_validator.define_critical_test_metrics()
    
    # Step 6: Save results
    analysis_id = f"ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Step 6: Saving analysis results with ID: {analysis_id}")
    discrepancy_detector.save_analysis_results(analysis_id)
    
    # Compile comprehensive report
    report = {
        'analysis_id': analysis_id,
        'timestamp': datetime.now().isoformat(),
        'production_baseline': prod_baseline,
        'production_patterns': prod_patterns,
        'pte_metrics': pte_metrics,
        'coverage_gaps': coverage_gaps,
        'discrepancies': [
            {
                'metric': d.metric_name,
                'prod_value': d.prod_value,
                'pte_value': d.pte_value,
                'discrepancy_pct': d.discrepancy_pct,
                'severity': d.severity,
                'recommendation': d.recommendation
            }
            for d in discrepancies
        ],
        'test_efficacy': efficacy_score,
        'critical_test_metrics': critical_metrics,
        'summary': {
            'total_discrepancies': len(discrepancies),
            'critical_issues': len([d for d in discrepancies if d.severity == 'critical']),
            'high_priority_issues': len([d for d in discrepancies if d.severity == 'high']),
            'overall_test_efficacy': efficacy_score.get('overall_efficacy_score', 0),
            'test_coverage_pct': coverage_gaps.get('coverage_percentage', 0)
        }
    }
    
    logger.info(f"Analysis complete. Found {len(discrepancies)} discrepancies")
    return report


def print_analysis_report(report: Dict):
    """Print formatted analysis report"""
    print("\n" + "="*100)
    print("PRODUCTION vs PTE TRAFFIC ANALYSIS REPORT")
    print("="*100)
    print(f"\nAnalysis ID: {report['analysis_id']}")
    print(f"Timestamp: {report['timestamp']}")
    
    print("\n" + "-"*100)
    print("EXECUTIVE SUMMARY")
    print("-"*100)
    summary = report['summary']
    print(f"Overall Test Efficacy Score: {summary['overall_test_efficacy']:.1f}%")
    print(f"Endpoint Coverage: {summary['test_coverage_pct']:.1f}%")
    print(f"Total Discrepancies Found: {summary['total_discrepancies']}")
    print(f"  - Critical Issues: {summary['critical_issues']}")
    print(f"  - High Priority Issues: {summary['high_priority_issues']}")
    
    print("\n" + "-"*100)
    print("PRODUCTION BASELINE (Last 24 Hours)")
    print("-"*100)
    baseline = report['production_baseline']
    if baseline:
        print(f"Peak Request Rate: {baseline.get('peak_request_rate', 0):.2f} req/s")
        print(f"Average Request Rate: {baseline.get('avg_request_rate', 0):.2f} req/s")
        print(f"P95 Response Time: {baseline.get('p95_response_time', 0):.2f} ms")
        print(f"P99 Response Time: {baseline.get('p99_response_time', 0):.2f} ms")
        print(f"Peak CPU Utilization: {baseline.get('peak_cpu', 0):.1f}%")
        print(f"Peak Memory Utilization: {baseline.get('peak_memory', 0):.1f}%")
        print(f"Max Error Rate: {baseline.get('max_error_rate', 0):.3f}%")
        print(f"Unique Endpoints: {baseline.get('unique_endpoints', 0)}")
    
    print("\n" + "-"*100)
    print("PTE TEST RESULTS")
    print("-"*100)
    pte = report['pte_metrics']
    if pte:
        print(f"Max Request Rate Tested: {pte.get('max_request_rate_tested', 0):.2f} req/s")
        print(f"Average Request Rate: {pte.get('avg_request_rate_tested', 0):.2f} req/s")
        print(f"P95 Response Time: {pte.get('p95_response_time', 0):.2f} ms")
        print(f"P99 Response Time: {pte.get('p99_response_time', 0):.2f} ms")
        print(f"Peak CPU: {pte.get('peak_cpu', 0):.1f}%")
        print(f"Peak Memory: {pte.get('peak_memory', 0):.1f}%")
        print(f"Max Error Rate: {pte.get('max_error_rate', 0):.3f}%")
        print(f"Endpoints Tested: {pte.get('unique_endpoints_tested', 0)}")
    
    print("\n" + "-"*100)
    print("CRITICAL DISCREPANCIES")
    print("-"*100)
    critical_discrepancies = [d for d in report['discrepancies'] 
                             if d['severity'] in ['critical', 'high']]
    
    if critical_discrepancies:
        for i, disc in enumerate(critical_discrepancies, 1):
            print(f"\n{i}. {disc['metric']} ({disc['severity'].upper()})")
            print(f"   Production Value: {disc['prod_value']:.2f}")
            print(f"   PTE Value: {disc['pte_value']:.2f}")
            print(f"   Discrepancy: {disc['discrepancy_pct']:.1f}%")
            print(f"   Recommendation: {disc['recommendation']}")
    else:
        print("No critical discrepancies found.")
    
    print("\n" + "-"*100)
    print("TEST COVERAGE GAPS")
    print("-"*100)
    coverage = report['coverage_gaps']
    if coverage:
        print(f"Total Production Endpoints: {coverage.get('total_prod_endpoints', 0)}")
        print(f"Tested Endpoints: {coverage.get('tested_endpoints', 0)}")
        print(f"Untested Endpoints: {coverage.get('untested_endpoints', 0)}")
        print(f"Coverage: {coverage.get('coverage_percentage', 0):.1f}%")
        
        if coverage.get('untested_list'):
            print("\nUntested Endpoints (Top 10):")
            for endpoint in coverage['untested_list'][:10]:
                print(f"  - {endpoint['http_method']} {endpoint['endpoint_name']}")
    
    print("\n" + "-"*100)
    print("CRITICAL TEST METRICS FOR NEXT CERTIFICATION")
    print("-"*100)
    metrics = report['critical_test_metrics']
    if metrics:
        print("\nLoad Testing:")
        load = metrics.get('load_testing', {})
        print(f"  Target Request Rate: {load.get('target_request_rate', 0):.2f} req/s")
        print(f"  Sustained Duration: {load.get('sustained_duration_minutes', 0)} minutes")
        print(f"  Spike Test Multiplier: {load.get('spike_test_multiplier', 0)}x")
        
        print("\nPerformance SLA:")
        perf = metrics.get('performance_sla', {})
        print(f"  Max P50 Response Time: {perf.get('max_p50_response_time_ms', 0):.2f} ms")
        print(f"  Max P95 Response Time: {perf.get('max_p95_response_time_ms', 0):.2f} ms")
        print(f"  Max P99 Response Time: {perf.get('max_p99_response_time_ms', 0):.2f} ms")
        
        print("\nReliability:")
        rel = metrics.get('reliability', {})
        print(f"  Max Error Rate: {rel.get('max_error_rate_pct', 0):.3f}%")
        print(f"  Required Uptime: {rel.get('required_uptime_pct', 0):.1f}%")
        
        print("\nResource Limits:")
        res = metrics.get('resource_limits', {})
        print(f"  Max CPU Utilization: {res.get('max_cpu_utilization_pct', 0):.1f}%")
        print(f"  Max Memory Utilization: {res.get('max_memory_utilization_pct', 0):.1f}%")
    
    print("\n" + "="*100)


def export_report_to_json(report: Dict, filename: str = None):
    """Export report to JSON file"""
    if filename is None:
        filename = f"analysis_report_{report['analysis_id']}.json"
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Report exported to {filename}")
    return filename


# Example usage
if __name__ == "__main__":
    # Database configuration
    db_config = {
        'username': 'your_username',
        'password': 'your_password',
        'dsn': 'hostname:1521/service_name'
    }
    
    try:
        # Run comprehensive analysis
        report = run_comprehensive_analysis(db_config, test_run_id=None)
        
        # Print formatted report
        print_analysis_report(report)
        
        # Export to JSON
        json_file = export_report_to_json(report)
        print(f"\nReport exported to: {json_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise
