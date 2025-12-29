"""
Production vs PTE Traffic Analysis System
Custom implementation for Oracle tables: PROD and PTE
Tables contain: api_endpoint, call_count, minduration, maxduration, avgduration, 
                90percentile, 95percentile, measuredate
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import cx_Oracle
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging
import urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EndpointMetrics:
    """Metrics for a specific API endpoint"""
    api_endpoint: str
    call_count: int
    min_duration: float
    max_duration: float
    avg_duration: float
    p90_duration: float
    p95_duration: float
    measure_date: datetime


@dataclass
class ComparisonResult:
    """Comparison result for an endpoint"""
    api_endpoint: str
    metric_name: str
    prod_value: float
    pte_value: float
    difference: float
    difference_pct: float
    severity: str
    status: str


class CustomOracleConnector:
    """Oracle Database connector for PROD and PTE tables with SQLAlchemy support"""
    
    def __init__(self, username: str, password: str, dsn: str):
        self.username = username
        self.password = password
        self.dsn = dsn
        self.engine = None
        self._create_engine()
    
    def _create_engine(self):
        """Create SQLAlchemy engine for Oracle"""
        try:
            # URL-encode the password to handle special characters
            encoded_password = urllib.parse.quote_plus(self.password)
            
            # Create connection string for Oracle
            # Format: oracle+cx_oracle://user:password@host:port/?service_name=service
            connection_string = f"oracle+cx_oracle://{self.username}:{encoded_password}@{self.dsn}"
            
            # Create engine with connection pooling disabled for better compatibility
            self.engine = create_engine(
                connection_string,
                poolclass=NullPool,
                echo=False
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM DUAL"))
            
            logger.info("SQLAlchemy engine created successfully")
            
        except Exception as e:
            logger.error(f"Error creating SQLAlchemy engine: {e}")
            logger.info("Falling back to cx_Oracle direct connection")
            self.engine = None
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if self.engine:
            # Use SQLAlchemy connection
            conn = self.engine.connect()
            try:
                yield conn
            finally:
                conn.close()
        else:
            # Fallback to cx_Oracle
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
    
    def fetch_prod_data(self, days_back: int = 7, endpoint_filter: str = None) -> pd.DataFrame:
        """Fetch production data using SQLAlchemy"""
        base_query = """
        SELECT 
            api_endpoint,
            call_count,
            minduration as min_duration,
            maxduration as max_duration,
            avgduration as avg_duration,
            "90PERCENTILE" as p90_duration,
            "95PERCENTILE" as p95_duration,
            measuredate as measure_date
        FROM prod
        WHERE measuredate >= SYSDATE - :days_back
        """
        
        if endpoint_filter:
            base_query += " AND UPPER(api_endpoint) LIKE UPPER(:endpoint_filter)"
        
        base_query += " ORDER BY measuredate DESC, api_endpoint"
        
        try:
            params = {'days_back': days_back}
            if endpoint_filter:
                params['endpoint_filter'] = f'%{endpoint_filter}%'
            
            if self.engine:
                # Use SQLAlchemy with pandas - no warning
                df = pd.read_sql(
                    text(base_query), 
                    self.engine, 
                    params=params
                )
            else:
                # Fallback to direct cx_Oracle connection
                with self.get_connection() as conn:
                    df = pd.read_sql(base_query, conn, params=params)
            
            df['measure_date'] = pd.to_datetime(df['measure_date'])
            logger.info(f"Fetched {len(df)} production records")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching production data: {e}")
            return pd.DataFrame()
    
    def fetch_pte_data(self, days_back: int = 30, endpoint_filter: str = None) -> pd.DataFrame:
        """Fetch PTE test data using SQLAlchemy"""
        base_query = """
        SELECT 
            api_endpoint,
            call_count,
            minduration as min_duration,
            maxduration as max_duration,
            avgduration as avg_duration,
            "90PERCENTILE" as p90_duration,
            "95PERCENTILE" as p95_duration,
            measuredate as measure_date
        FROM pte
        WHERE measuredate >= SYSDATE - :days_back
        """
        
        if endpoint_filter:
            base_query += " AND UPPER(api_endpoint) LIKE UPPER(:endpoint_filter)"
        
        base_query += " ORDER BY measuredate DESC, api_endpoint"
        
        try:
            params = {'days_back': days_back}
            if endpoint_filter:
                params['endpoint_filter'] = f'%{endpoint_filter}%'
            
            if self.engine:
                # Use SQLAlchemy with pandas - no warning
                df = pd.read_sql(
                    text(base_query), 
                    self.engine, 
                    params=params
                )
            else:
                # Fallback to direct cx_Oracle connection
                with self.get_connection() as conn:
                    df = pd.read_sql(base_query, conn, params=params)
            
            df['measure_date'] = pd.to_datetime(df['measure_date'])
            logger.info(f"Fetched {len(df)} PTE records")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching PTE data: {e}")
            return pd.DataFrame()
    
    def get_endpoint_coverage(self) -> Dict:
        """Get endpoint coverage comparison"""
        query = """
        WITH prod_endpoints AS (
            SELECT DISTINCT api_endpoint
            FROM prod
            WHERE measuredate >= SYSDATE - 7
        ),
        pte_endpoints AS (
            SELECT DISTINCT api_endpoint
            FROM pte
            WHERE measuredate >= SYSDATE - 30
        )
        SELECT 
            p.api_endpoint,
            CASE WHEN t.api_endpoint IS NOT NULL THEN 'Y' ELSE 'N' END as tested_in_pte
        FROM prod_endpoints p
        LEFT JOIN pte_endpoints t ON p.api_endpoint = t.api_endpoint
        ORDER BY tested_in_pte, p.api_endpoint
        """
        
        try:
            if self.engine:
                df = pd.read_sql(text(query), self.engine)
            else:
                with self.get_connection() as conn:
                    df = pd.read_sql(query, conn)
            
            tested = len(df[df['tested_in_pte'] == 'Y'])
            total = len(df)
            untested_list = df[df['tested_in_pte'] == 'N']['api_endpoint'].tolist()
            
            return {
                'total_endpoints': total,
                'tested_endpoints': tested,
                'untested_endpoints': total - tested,
                'coverage_percentage': (tested / total * 100) if total > 0 else 0,
                'untested_list': untested_list
            }
        except Exception as e:
            logger.error(f"Error getting endpoint coverage: {e}")
            return {}
    
    def save_comparison_results(self, results: List[ComparisonResult], analysis_id: str):
        """Save comparison results to database"""
        insert_query = """
        INSERT INTO prod_pte_comparison (
            analysis_id, api_endpoint, metric_name, prod_value, pte_value,
            difference, difference_pct, severity, status, created_date
        ) VALUES (
            :analysis_id, :api_endpoint, :metric_name, :prod_value, :pte_value,
            :difference, :difference_pct, :severity, :status, SYSDATE
        )
        """
        
        try:
            if self.engine:
                with self.engine.begin() as conn:
                    for result in results:
                        conn.execute(text(insert_query), {
                            'analysis_id': analysis_id,
                            'api_endpoint': result.api_endpoint,
                            'metric_name': result.metric_name,
                            'prod_value': result.prod_value,
                            'pte_value': result.pte_value,
                            'difference': result.difference,
                            'difference_pct': result.difference_pct,
                            'severity': result.severity,
                            'status': result.status
                        })
                logger.info(f"Saved {len(results)} comparison results")
            else:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    for result in results:
                        cursor.execute(insert_query, {
                            'analysis_id': analysis_id,
                            'api_endpoint': result.api_endpoint,
                            'metric_name': result.metric_name,
                            'prod_value': result.prod_value,
                            'pte_value': result.pte_value,
                            'difference': result.difference,
                            'difference_pct': result.difference_pct,
                            'severity': result.severity,
                            'status': result.status
                        })
                    conn.commit()
                logger.info(f"Saved {len(results)} comparison results")
        except Exception as e:
            logger.error(f"Error saving comparison results: {e}")
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine disposed")


class ProductionDataAnalyzer:
    """Analyze production data"""
    
    def __init__(self, db_connector: CustomOracleConnector):
        self.db = db_connector
    
    def get_aggregated_metrics(self, days_back: int = 7) -> Dict:
        """Get aggregated production metrics"""
        df = self.db.fetch_prod_data(days_back=days_back)
        
        if df.empty:
            return {}
        
        metrics = {
            'total_calls': int(df['call_count'].sum()),
            'total_endpoints': int(df['api_endpoint'].nunique()),
            'avg_call_count_per_endpoint': float(df.groupby('api_endpoint')['call_count'].sum().mean()),
            'peak_call_count': int(df.groupby('api_endpoint')['call_count'].sum().max()),
            'overall_avg_duration': float(df['avg_duration'].mean()),
            'overall_p90_duration': float(df['p90_duration'].quantile(0.90)),
            'overall_p95_duration': float(df['p95_duration'].quantile(0.95)),
            'slowest_endpoint': df.loc[df['avg_duration'].idxmax(), 'api_endpoint'] if len(df) > 0 else None,
            'slowest_avg_duration': float(df['avg_duration'].max()),
            'fastest_endpoint': df.loc[df['avg_duration'].idxmin(), 'api_endpoint'] if len(df) > 0 else None,
            'fastest_avg_duration': float(df['avg_duration'].min()),
            'measurement_days': days_back,
            'date_range_start': df['measure_date'].min().isoformat() if len(df) > 0 else None,
            'date_range_end': df['measure_date'].max().isoformat() if len(df) > 0 else None
        }
        
        return metrics
    
    def get_top_endpoints_by_volume(self, top_n: int = 10, days_back: int = 7) -> pd.DataFrame:
        """Get top endpoints by call volume"""
        df = self.db.fetch_prod_data(days_back=days_back)
        
        if df.empty:
            return pd.DataFrame()
        
        top_endpoints = (df.groupby('api_endpoint')
                        .agg({
                            'call_count': 'sum',
                            'avg_duration': 'mean',
                            'p95_duration': 'mean'
                        })
                        .sort_values('call_count', ascending=False)
                        .head(top_n))
        
        return top_endpoints.reset_index()
    
    def get_slowest_endpoints(self, top_n: int = 10, days_back: int = 7) -> pd.DataFrame:
        """Get slowest endpoints by average duration"""
        df = self.db.fetch_prod_data(days_back=days_back)
        
        if df.empty:
            return pd.DataFrame()
        
        slowest = (df.groupby('api_endpoint')
                  .agg({
                      'call_count': 'sum',
                      'avg_duration': 'mean',
                      'p90_duration': 'mean',
                      'p95_duration': 'mean'
                  })
                  .sort_values('avg_duration', ascending=False)
                  .head(top_n))
        
        return slowest.reset_index()


class PTEDataAnalyzer:
    """Analyze PTE test data"""
    
    def __init__(self, db_connector: CustomOracleConnector):
        self.db = db_connector
    
    def get_aggregated_metrics(self, days_back: int = 30) -> Dict:
        """Get aggregated PTE metrics"""
        df = self.db.fetch_pte_data(days_back=days_back)
        
        if df.empty:
            return {}
        
        metrics = {
            'total_calls': int(df['call_count'].sum()),
            'total_endpoints_tested': int(df['api_endpoint'].nunique()),
            'avg_call_count_per_endpoint': float(df.groupby('api_endpoint')['call_count'].sum().mean()),
            'peak_call_count': int(df.groupby('api_endpoint')['call_count'].sum().max()),
            'overall_avg_duration': float(df['avg_duration'].mean()),
            'overall_p90_duration': float(df['p90_duration'].quantile(0.90)),
            'overall_p95_duration': float(df['p95_duration'].quantile(0.95)),
            'slowest_endpoint': df.loc[df['avg_duration'].idxmax(), 'api_endpoint'] if len(df) > 0 else None,
            'slowest_avg_duration': float(df['avg_duration'].max()),
            'measurement_days': days_back,
            'date_range_start': df['measure_date'].min().isoformat() if len(df) > 0 else None,
            'date_range_end': df['measure_date'].max().isoformat() if len(df) > 0 else None
        }
        
        return metrics


class EndpointComparator:
    """Compare production and PTE data for endpoints"""
    
    def __init__(self, db_connector: CustomOracleConnector, thresholds: Dict = None):
        self.db = db_connector
        self.thresholds = thresholds or {
            'call_count_variance_pct': 30,  # 30% variance threshold
            'duration_variance_pct': 20,     # 20% variance threshold
            'p95_variance_pct': 25           # 25% variance threshold
        }
    
    def compare_endpoints(self, prod_days: int = 7, pte_days: int = 30) -> List[ComparisonResult]:
        """Compare all common endpoints between prod and PTE"""
        prod_df = self.db.fetch_prod_data(days_back=prod_days)
        pte_df = self.db.fetch_pte_data(days_back=pte_days)
        
        if prod_df.empty or pte_df.empty:
            logger.warning("No data available for comparison")
            return []
        
        # Aggregate by endpoint
        prod_agg = self._aggregate_by_endpoint(prod_df)
        pte_agg = self._aggregate_by_endpoint(pte_df)
        
        # Find common endpoints
        common_endpoints = set(prod_agg.index) & set(pte_agg.index)
        
        results = []
        for endpoint in common_endpoints:
            prod_data = prod_agg.loc[endpoint]
            pte_data = pte_agg.loc[endpoint]
            
            # Compare call count
            results.append(self._compare_metric(
                endpoint, 'call_count', 
                prod_data['call_count'], 
                pte_data['call_count'],
                self.thresholds['call_count_variance_pct'],
                lower_is_better=False
            ))
            
            # Compare average duration
            results.append(self._compare_metric(
                endpoint, 'avg_duration',
                prod_data['avg_duration'],
                pte_data['avg_duration'],
                self.thresholds['duration_variance_pct'],
                lower_is_better=True
            ))
            
            # Compare P90 duration
            results.append(self._compare_metric(
                endpoint, 'p90_duration',
                prod_data['p90_duration'],
                pte_data['p90_duration'],
                self.thresholds['duration_variance_pct'],
                lower_is_better=True
            ))
            
            # Compare P95 duration
            results.append(self._compare_metric(
                endpoint, 'p95_duration',
                prod_data['p95_duration'],
                pte_data['p95_duration'],
                self.thresholds['p95_variance_pct'],
                lower_is_better=True
            ))
        
        return results
    
    def _aggregate_by_endpoint(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate data by endpoint"""
        return df.groupby('api_endpoint').agg({
            'call_count': 'sum',
            'min_duration': 'min',
            'max_duration': 'max',
            'avg_duration': 'mean',
            'p90_duration': 'mean',
            'p95_duration': 'mean'
        })
    
    def _compare_metric(self, endpoint: str, metric_name: str, 
                       prod_value: float, pte_value: float,
                       threshold_pct: float, lower_is_better: bool) -> ComparisonResult:
        """Compare a single metric"""
        if prod_value == 0:
            difference_pct = 0
        else:
            difference_pct = ((pte_value - prod_value) / prod_value) * 100
        
        difference = pte_value - prod_value
        
        # Determine severity
        abs_diff_pct = abs(difference_pct)
        if abs_diff_pct > threshold_pct * 1.5:
            severity = 'critical'
        elif abs_diff_pct > threshold_pct:
            severity = 'high'
        elif abs_diff_pct > threshold_pct * 0.5:
            severity = 'medium'
        else:
            severity = 'low'
        
        # Determine status
        if lower_is_better:
            # For duration metrics, lower is better
            if pte_value <= prod_value * (1 + threshold_pct/100):
                status = 'pass'
            else:
                status = 'fail'
        else:
            # For call count, higher is better (testing more load)
            if pte_value >= prod_value * 0.7:  # At least 70% of prod load
                status = 'pass'
            else:
                status = 'fail'
        
        return ComparisonResult(
            api_endpoint=endpoint,
            metric_name=metric_name,
            prod_value=prod_value,
            pte_value=pte_value,
            difference=difference,
            difference_pct=difference_pct,
            severity=severity,
            status=status
        )
    
    def get_critical_issues(self, results: List[ComparisonResult]) -> List[ComparisonResult]:
        """Filter critical and high severity issues"""
        return [r for r in results if r.severity in ['critical', 'high'] and r.status == 'fail']


def run_custom_analysis(db_config: Dict, prod_days: int = 7, pte_days: int = 30) -> Dict:
    """
    Main analysis function for custom PROD and PTE tables
    
    Args:
        db_config: Database configuration
        prod_days: Days of production data to analyze
        pte_days: Days of PTE data to analyze
    
    Returns:
        Comprehensive analysis report
    """
    logger.info("Starting custom production vs PTE analysis")
    
    # Initialize connector
    db = CustomOracleConnector(
        username=db_config['username'],
        password=db_config['password'],
        dsn=db_config['dsn']
    )
    
    # Initialize analyzers
    prod_analyzer = ProductionDataAnalyzer(db)
    pte_analyzer = PTEDataAnalyzer(db)
    comparator = EndpointComparator(db)
    
    # Step 1: Get production metrics
    logger.info("Analyzing production data...")
    prod_metrics = prod_analyzer.get_aggregated_metrics(days_back=prod_days)
    top_volume_endpoints = prod_analyzer.get_top_endpoints_by_volume(top_n=10, days_back=prod_days)
    slowest_endpoints = prod_analyzer.get_slowest_endpoints(top_n=10, days_back=prod_days)
    
    # Step 2: Get PTE metrics
    logger.info("Analyzing PTE data...")
    pte_metrics = pte_analyzer.get_aggregated_metrics(days_back=pte_days)
    
    # Step 3: Compare endpoints
    logger.info("Comparing endpoints...")
    comparison_results = comparator.compare_endpoints(prod_days=prod_days, pte_days=pte_days)
    critical_issues = comparator.get_critical_issues(comparison_results)
    
    # Step 4: Get coverage
    logger.info("Analyzing endpoint coverage...")
    coverage = db.get_endpoint_coverage()
    
    # Step 5: Save results
    analysis_id = f"ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    db.save_comparison_results(comparison_results, analysis_id)
    
    # Compile report
    report = {
        'analysis_id': analysis_id,
        'timestamp': datetime.now().isoformat(),
        'production_metrics': prod_metrics,
        'pte_metrics': pte_metrics,
        'top_volume_endpoints': top_volume_endpoints.to_dict('records') if not top_volume_endpoints.empty else [],
        'slowest_endpoints': slowest_endpoints.to_dict('records') if not slowest_endpoints.empty else [],
        'comparison_results': [
            {
                'api_endpoint': r.api_endpoint,
                'metric_name': r.metric_name,
                'prod_value': r.prod_value,
                'pte_value': r.pte_value,
                'difference': r.difference,
                'difference_pct': r.difference_pct,
                'severity': r.severity,
                'status': r.status
            }
            for r in comparison_results
        ],
        'critical_issues': [
            {
                'api_endpoint': r.api_endpoint,
                'metric_name': r.metric_name,
                'prod_value': r.prod_value,
                'pte_value': r.pte_value,
                'difference_pct': r.difference_pct,
                'severity': r.severity
            }
            for r in critical_issues
        ],
        'coverage': coverage,
        'summary': {
            'total_comparisons': len(comparison_results),
            'critical_issues': len([r for r in comparison_results if r.severity == 'critical']),
            'high_issues': len([r for r in comparison_results if r.severity == 'high']),
            'failed_tests': len([r for r in comparison_results if r.status == 'fail']),
            'passed_tests': len([r for r in comparison_results if r.status == 'pass']),
            'coverage_pct': coverage.get('coverage_percentage', 0)
        }
    }
    
    logger.info(f"Analysis complete. Analysis ID: {analysis_id}")
    return report


def print_custom_report(report: Dict):
    """Print formatted report for custom analysis"""
    print("\n" + "="*100)
    print("PRODUCTION vs PTE API ENDPOINT ANALYSIS")
    print("="*100)
    print(f"\nAnalysis ID: {report['analysis_id']}")
    print(f"Timestamp: {report['timestamp']}")
    
    print("\n" + "-"*100)
    print("SUMMARY")
    print("-"*100)
    summary = report['summary']
    print(f"Total Comparisons: {summary['total_comparisons']}")
    print(f"Critical Issues: {summary['critical_issues']}")
    print(f"High Issues: {summary['high_issues']}")
    print(f"Failed Tests: {summary['failed_tests']}")
    print(f"Passed Tests: {summary['passed_tests']}")
    print(f"Endpoint Coverage: {summary['coverage_pct']:.1f}%")
    
    print("\n" + "-"*100)
    print("PRODUCTION METRICS")
    print("-"*100)
    prod = report['production_metrics']
    if prod:
        print(f"Total API Calls: {prod.get('total_calls', 0):,}")
        print(f"Total Endpoints: {prod.get('total_endpoints', 0)}")
        print(f"Average Duration: {prod.get('overall_avg_duration', 0):.2f} ms")
        print(f"P90 Duration: {prod.get('overall_p90_duration', 0):.2f} ms")
        print(f"P95 Duration: {prod.get('overall_p95_duration', 0):.2f} ms")
        print(f"Slowest Endpoint: {prod.get('slowest_endpoint', 'N/A')} ({prod.get('slowest_avg_duration', 0):.2f} ms)")
    
    print("\n" + "-"*100)
    print("PTE METRICS")
    print("-"*100)
    pte = report['pte_metrics']
    if pte:
        print(f"Total API Calls: {pte.get('total_calls', 0):,}")
        print(f"Endpoints Tested: {pte.get('total_endpoints_tested', 0)}")
        print(f"Average Duration: {pte.get('overall_avg_duration', 0):.2f} ms")
        print(f"P90 Duration: {pte.get('overall_p90_duration', 0):.2f} ms")
        print(f"P95 Duration: {pte.get('overall_p95_duration', 0):.2f} ms")
    
    print("\n" + "-"*100)
    print("CRITICAL ISSUES")
    print("-"*100)
    if report['critical_issues']:
        for i, issue in enumerate(report['critical_issues'][:10], 1):
            print(f"\n{i}. {issue['api_endpoint']} - {issue['metric_name']}")
            print(f"   Production: {issue['prod_value']:.2f}")
            print(f"   PTE: {issue['pte_value']:.2f}")
            print(f"   Difference: {issue['difference_pct']:.1f}%")
            print(f"   Severity: {issue['severity'].upper()}")
    else:
        print("No critical issues found!")
    
    print("\n" + "-"*100)
    print("TOP 5 ENDPOINTS BY VOLUME")
    print("-"*100)
    for i, endpoint in enumerate(report['top_volume_endpoints'][:5], 1):
        print(f"{i}. {endpoint['api_endpoint']}")
        print(f"   Calls: {endpoint['call_count']:,} | Avg Duration: {endpoint['avg_duration']:.2f} ms")
    
    print("\n" + "="*100)


# Example usage
if __name__ == "__main__":
    db_config = {
        'username': 'your_username',
        'password': 'your_password',
        'dsn': 'hostname:1521/service_name'  # or TNS name
    }
    
    try:
        # Run analysis
        report = run_custom_analysis(db_config, prod_days=7, pte_days=30)
        
        # Print report
        print_custom_report(report)
        
        # Export to JSON
        import json
        with open(f"analysis_{report['analysis_id']}.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nAnalysis complete! Report saved to analysis_{report['analysis_id']}.json")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        