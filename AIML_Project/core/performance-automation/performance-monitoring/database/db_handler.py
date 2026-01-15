"""
Database Handler for storing monitoring data - Oracle DB Version
"""
import cx_Oracle
from typing import List, Dict, Optional, Any
from datetime import datetime
from utils.logger import setup_logger

class MonitoringDataDB:
    """Handle Oracle database operations for monitoring data"""
    
    def __init__(self, username: str, password: str, dsn: str, **kwargs):
        """
        Initialize Oracle database connection
        
        Args:
            username: Oracle username
            password: Oracle password
            dsn: Data Source Name (host:port/service_name)
                 Example: 'localhost:1521/ORCL' or '10.0.0.1:1521/XEPDB1'
        """
        self.connection = None
        self.logger = setup_logger('OracleDBHandler')
        
        try:
            # Initialize Oracle client if needed
            # cx_Oracle.init_oracle_client(lib_dir="/path/to/instantclient")
            
            self.connection = cx_Oracle.connect(
                user=username,
                password=password,
                dsn=dsn,
                encoding="UTF-8"
            )
            self.connection.autocommit = False
            self.logger.info(f"✓ Connected to Oracle database: {dsn}")
            
            self.create_tables()
            
        except cx_Oracle.Error as e:
            error, = e.args
            self.logger.error(f"✗ Oracle connection error: {error.message}")
            raise
    
    def create_tables(self):
        """Create all required tables in Oracle"""
        cursor = self.connection.cursor()
        
        try:
            # Drop existing sequences if recreating
            sequences = [
                'test_runs_seq',
                'appdynamics_metrics_seq',
                'kibana_data_seq'
            ]
            
            for seq in sequences:
                try:
                    cursor.execute(f"DROP SEQUENCE {seq}")
                except cx_Oracle.DatabaseError:
                    pass  # Sequence doesn't exist
            
            # Test runs table
            cursor.execute('''
                CREATE TABLE test_runs (
                    id NUMBER PRIMARY KEY,
                    test_run_id VARCHAR2(100) UNIQUE NOT NULL,
                    test_name VARCHAR2(200),
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_minutes NUMBER,
                    status VARCHAR2(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE SEQUENCE test_runs_seq START WITH 1 INCREMENT BY 1')
            cursor.execute('CREATE INDEX idx_test_run_id ON test_runs(test_run_id)')
            cursor.execute('CREATE INDEX idx_start_time ON test_runs(start_time)')
            
            self.logger.info("✓ Created test_runs table")
            
        except cx_Oracle.DatabaseError as e:
            if 'ORA-00955' in str(e):  # Table already exists
                self.logger.info("ℹ test_runs table already exists")
            else:
                raise
        
        try:
            # AppDynamics metrics table
            cursor.execute('''
                CREATE TABLE appdynamics_metrics (
                    id NUMBER PRIMARY KEY,
                    test_run_id VARCHAR2(100) NOT NULL,
                    app_name VARCHAR2(100),
                    tier_name VARCHAR2(100),
                    node_name VARCHAR2(100),
                    metric_category VARCHAR2(50),
                    metric_name VARCHAR2(200),
                    metric_path VARCHAR2(500),
                    metric_value BINARY_DOUBLE,
                    metric_count NUMBER,
                    metric_min BINARY_DOUBLE,
                    metric_max BINARY_DOUBLE,
                    metric_sum BINARY_DOUBLE,
                    timestamp NUMBER(19),
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_appd_test_run FOREIGN KEY (test_run_id) 
                        REFERENCES test_runs(test_run_id)
                )
            ''')
            
            cursor.execute('CREATE SEQUENCE appdynamics_metrics_seq START WITH 1 INCREMENT BY 1')
            cursor.execute('CREATE INDEX idx_appd_test_run ON appdynamics_metrics(test_run_id)')
            cursor.execute('CREATE INDEX idx_appd_metric_name ON appdynamics_metrics(metric_name)')
            cursor.execute('CREATE INDEX idx_appd_timestamp ON appdynamics_metrics(timestamp)')
            
            self.logger.info("✓ Created appdynamics_metrics table")
            
        except cx_Oracle.DatabaseError as e:
            if 'ORA-00955' in str(e):
                self.logger.info("ℹ appdynamics_metrics table already exists")
            else:
                raise
        
        try:
            # Kibana data table
            cursor.execute('''
                CREATE TABLE kibana_data (
                    id NUMBER PRIMARY KEY,
                    test_run_id VARCHAR2(100) NOT NULL,
                    visualization_id VARCHAR2(100),
                    visualization_name VARCHAR2(200),
                    data_type VARCHAR2(50),
                    data_key VARCHAR2(200),
                    data_value CLOB,
                    timestamp NUMBER(19),
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_kibana_test_run FOREIGN KEY (test_run_id) 
                        REFERENCES test_runs(test_run_id)
                )
            ''')
            
            cursor.execute('CREATE SEQUENCE kibana_data_seq START WITH 1 INCREMENT BY 1')
            cursor.execute('CREATE INDEX idx_kibana_test_run ON kibana_data(test_run_id)')
            cursor.execute('CREATE INDEX idx_kibana_viz_id ON kibana_data(visualization_id)')
            cursor.execute('CREATE INDEX idx_kibana_timestamp ON kibana_data(timestamp)')
            
            self.logger.info("✓ Created kibana_data table")
            
        except cx_Oracle.DatabaseError as e:
            if 'ORA-00955' in str(e):
                self.logger.info("ℹ kibana_data table already exists")
            else:
                raise
        
        self.connection.commit()
        self.logger.info("✓ All database tables verified/created")
    
    def insert_test_run(self, test_run_id: str, test_name: str = None, 
                       start_time: datetime = None, duration_minutes: int = None):
        """Insert new test run record"""
        cursor = self.connection.cursor()
        
        if start_time is None:
            start_time = datetime.now()
        
        try:
            cursor.execute('''
                INSERT INTO test_runs (id, test_run_id, test_name, start_time, duration_minutes, status)
                VALUES (test_runs_seq.NEXTVAL, :1, :2, :3, :4, :5)
            ''', (test_run_id, test_name, start_time, duration_minutes, 'running'))
            
            self.connection.commit()
            self.logger.info(f"✓ Test run created: {test_run_id}")
            
        except cx_Oracle.Error as e:
            error, = e.args
            self.logger.error(f"✗ Error inserting test run: {error.message}")
            self.connection.rollback()
    
    def update_test_run_status(self, test_run_id: str, status: str, end_time: datetime = None):
        """Update test run status"""
        cursor = self.connection.cursor()
        
        if end_time is None:
            end_time = datetime.now()
        
        try:
            cursor.execute('''
                UPDATE test_runs 
                SET status = :1, end_time = :2
                WHERE test_run_id = :3
            ''', (status, end_time, test_run_id))
            
            self.connection.commit()
            self.logger.info(f"✓ Test run updated: {test_run_id} - {status}")
            
        except cx_Oracle.Error as e:
            error, = e.args
            self.logger.error(f"✗ Error updating test run: {error.message}")
            self.connection.rollback()
    
    def insert_appdynamics_metrics(self, test_run_id: str, app_name: str, 
                                   tier_name: str, node_name: str,
                                   metrics_data: Dict[str, Dict[str, List[Dict]]]):
        """Insert AppDynamics metrics data"""
        cursor = self.connection.cursor()
        inserted_count = 0
        
        try:
            for category, metrics in metrics_data.items():
                for metric_name, values in metrics.items():
                    if not values:
                        continue
                    
                    for value_point in values:
                        cursor.execute('''
                            INSERT INTO appdynamics_metrics 
                            (id, test_run_id, app_name, tier_name, node_name, metric_category,
                             metric_name, metric_path, metric_value, metric_count, 
                             metric_min, metric_max, metric_sum, timestamp)
                            VALUES (appdynamics_metrics_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13)
                        ''', (
                            test_run_id,
                            app_name,
                            tier_name,
                            node_name,
                            category,
                            metric_name,
                            value_point.get('metric_path', ''),
                            value_point.get('value'),
                            value_point.get('count'),
                            value_point.get('min'),
                            value_point.get('max'),
                            value_point.get('sum'),
                            value_point.get('timestamp')
                        ))
                        inserted_count += 1
            
            self.connection.commit()
            self.logger.info(f"✓ Inserted {inserted_count} AppDynamics metric records")
            
        except cx_Oracle.Error as e:
            error, = e.args
            self.logger.error(f"✗ Error inserting AppDynamics metrics: {error.message}")
            self.connection.rollback()
    
    def insert_kibana_data(self, test_run_id: str, visualization_id: str,
                          visualization_name: str, data: List[Dict], 
                          timestamp: int = None):
        """Insert Kibana visualization data"""
        cursor = self.connection.cursor()
        inserted_count = 0
        
        if timestamp is None:
            timestamp = int(datetime.now().timestamp() * 1000)
        
        try:
            for item in data:
                for key, value in item.items():
                    cursor.execute('''
                        INSERT INTO kibana_data 
                        (id, test_run_id, visualization_id, visualization_name, 
                         data_type, data_key, data_value, timestamp)
                        VALUES (kibana_data_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7)
                    ''', (
                        test_run_id,
                        visualization_id,
                        visualization_name,
                        type(value).__name__,
                        key,
                        str(value),
                        timestamp
                    ))
                    inserted_count += 1
            
            self.connection.commit()
            self.logger.info(f"✓ Inserted {inserted_count} Kibana data records")
            
        except cx_Oracle.Error as e:
            error, = e.args
            self.logger.error(f"✗ Error inserting Kibana data: {error.message}")
            self.connection.rollback()
    
    def get_test_run_metrics(self, test_run_id: str) -> Dict:
        """Retrieve all metrics for a test run"""
        cursor = self.connection.cursor()
        
        result = {
            'test_run': None,
            'appdynamics_metrics': [],
            'kibana_data': []
        }
        
        try:
            # Get test run info
            cursor.execute('''
                SELECT * FROM test_runs WHERE test_run_id = :1
            ''', (test_run_id,))
            
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                result['test_run'] = dict(zip(columns, row))
            
            # Get AppDynamics metrics
            cursor.execute('''
                SELECT * FROM appdynamics_metrics 
                WHERE test_run_id = :1
                ORDER BY timestamp
            ''', (test_run_id,))
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            result['appdynamics_metrics'] = [dict(zip(columns, row)) for row in rows]
            
            # Get Kibana data
            cursor.execute('''
                SELECT * FROM kibana_data 
                WHERE test_run_id = :1
                ORDER BY timestamp
            ''', (test_run_id,))
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            result['kibana_data'] = [dict(zip(columns, row)) for row in rows]
            
            self.logger.info(f"✓ Retrieved metrics for test run: {test_run_id}")
            return result
            
        except cx_Oracle.Error as e:
            error, = e.args
            self.logger.error(f"✗ Error retrieving test run metrics: {error.message}")
            return result
    
    def get_metrics_summary(self, test_run_id: str) -> Dict:
        """Get aggregated metrics summary"""
        cursor = self.connection.cursor()
        summary = {}
        
        try:
            # AppDynamics metrics summary
            cursor.execute('''
                SELECT 
                    metric_category,
                    metric_name,
                    COUNT(*) as data_points,
                    AVG(metric_value) as avg_value,
                    MIN(metric_value) as min_value,
                    MAX(metric_value) as max_value
                FROM appdynamics_metrics
                WHERE test_run_id = :1
                GROUP BY metric_category, metric_name
                ORDER BY metric_category, metric_name
            ''', (test_run_id,))
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            summary['appdynamics'] = [dict(zip(columns, row)) for row in rows]
            
            # Kibana data summary
            cursor.execute('''
                SELECT 
                    visualization_name,
                    COUNT(*) as data_points
                FROM kibana_data
                WHERE test_run_id = :1
                GROUP BY visualization_name
            ''', (test_run_id,))
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            summary['kibana'] = [dict(zip(columns, row)) for row in rows]
            
            return summary
            
        except cx_Oracle.Error as e:
            error, = e.args
            self.logger.error(f"✗ Error getting metrics summary: {error.message}")
            return summary
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.logger.info("✓ Oracle database connection closed")
    def insert_appdynamics_dashboard_metrics(self, test_run_id: str, 
                                             dashboard_data: Dict[str, Dict]):
        """
        Insert AppDynamics dashboard metrics data with widget organization
        
        Args:
            test_run_id: Test run identifier
            dashboard_data: Dictionary from get_dashboard_metrics()
        """
        cursor = self.connection.cursor()
        inserted_count = 0
        
        try:
            for widget_name, widget_data in dashboard_data.items():
                if 'error' in widget_data:
                    self.logger.warning(f"Skipping widget {widget_name} due to error: {widget_data['error']}")
                    continue
                
                app_name = widget_data.get('app_name')
                tier_name = widget_data.get('tier_name')
                metric_type = widget_data.get('metric_type')
                metrics = widget_data.get('metrics', {})
                
                if metric_type == 'jvm':
                    # JVM metrics organized by node
                    for node_name, node_metrics in metrics.items():
                        for metric_name, values in node_metrics.items():
                            for value_point in values:
                                cursor.execute('''
                                    INSERT INTO appdynamics_metrics 
                                    (id, test_run_id, app_name, tier_name, node_name, metric_category,
                                     metric_name, metric_path, metric_value, metric_count, 
                                     metric_min, metric_max, metric_sum, timestamp)
                                    VALUES (appdynamics_metrics_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13)
                                ''', (
                                    test_run_id,
                                    app_name,
                                    tier_name,
                                    node_name,
                                    'jvm',
                                    metric_name,
                                    value_point.get('metric_path', ''),
                                    value_point.get('value'),
                                    value_point.get('count'),
                                    value_point.get('min'),
                                    value_point.get('max'),
                                    value_point.get('sum'),
                                    value_point.get('timestamp')
                                ))
                                inserted_count += 1
                
                elif metric_type == 'transaction':
                    # Transaction metrics for tier
                    tier_metrics = metrics.get('tier_metrics', {})
                    for metric_name, values in tier_metrics.items():
                        for value_point in values:
                            cursor.execute('''
                                INSERT INTO appdynamics_metrics 
                                (id, test_run_id, app_name, tier_name, node_name, metric_category,
                                 metric_name, metric_path, metric_value, metric_count, 
                                 metric_min, metric_max, metric_sum, timestamp)
                                VALUES (appdynamics_metrics_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13)
                            ''', (
                                test_run_id,
                                app_name,
                                tier_name,
                                'TIER_LEVEL',  # No specific node for tier-level metrics
                                'transaction',
                                metric_name,
                                value_point.get('metric_path', ''),
                                value_point.get('value'),
                                value_point.get('count'),
                                value_point.get('min'),
                                value_point.get('max'),
                                value_point.get('sum'),
                                value_point.get('timestamp')
                            ))
                            inserted_count += 1
                
                elif metric_type == 'combined':
                    # Both JVM and transaction metrics
                    jvm_data = metrics.get('jvm', {})
                    transaction_data = metrics.get('transaction', {})
                    
                    # Insert JVM metrics
                    for node_name, node_metrics in jvm_data.items():
                        for metric_name, values in node_metrics.items():
                            for value_point in values:
                                cursor.execute('''
                                    INSERT INTO appdynamics_metrics 
                                    (id, test_run_id, app_name, tier_name, node_name, metric_category,
                                     metric_name, metric_path, metric_value, metric_count, 
                                     metric_min, metric_max, metric_sum, timestamp)
                                    VALUES (appdynamics_metrics_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13)
                                ''', (
                                    test_run_id,
                                    app_name,
                                    tier_name,
                                    node_name,
                                    'jvm',
                                    metric_name,
                                    value_point.get('metric_path', ''),
                                    value_point.get('value'),
                                    value_point.get('count'),
                                    value_point.get('min'),
                                    value_point.get('max'),
                                    value_point.get('sum'),
                                    value_point.get('timestamp')
                                ))
                                inserted_count += 1
                    
                    # Insert transaction metrics
                    for metric_name, values in transaction_data.items():
                        for value_point in values:
                            cursor.execute('''
                                INSERT INTO appdynamics_metrics 
                                (id, test_run_id, app_name, tier_name, node_name, metric_category,
                                 metric_name, metric_path, metric_value, metric_count, 
                                 metric_min, metric_max, metric_sum, timestamp)
                                VALUES (appdynamics_metrics_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13)
                            ''', (
                                test_run_id,
                                app_name,
                                tier_name,
                                'TIER_LEVEL',
                                'transaction',
                                metric_name,
                                value_point.get('metric_path', ''),
                                value_point.get('value'),
                                value_point.get('count'),
                                value_point.get('min'),
                                value_point.get('max'),
                                value_point.get('sum'),
                                value_point.get('timestamp')
                            ))
                            inserted_count += 1
            
            self.connection.commit()
            self.logger.info(f"✓ Inserted {inserted_count} AppDynamics dashboard metric records")
            
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'args'):
                error_msg = e.args[0].message if hasattr(e.args[0], 'message') else str(e)
            self.logger.error(f"✗ Error inserting AppDynamics dashboard metrics: {error_msg}")
            self.connection.rollback()        