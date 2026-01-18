"""
Database Handler for Oracle - Complete Schema
"""
import cx_Oracle
from typing import List, Dict, Optional
from datetime import datetime
from utils.logger import setup_logger

class MonitoringDataDB:
    """Handle Oracle database operations"""
    
    def __init__(self, username: str, password: str, dsn: str):
        self.connection = None
        self.logger = setup_logger('OracleDB')
        
        try:
            self.connection = cx_Oracle.connect(
                user=username,
                password=password,
                dsn=dsn,
                encoding="UTF-8"
            )
            self.connection.autocommit = False
            self.logger.info(f"✓ Connected to Oracle: {dsn}")
            self.create_tables()
            
        except cx_Oracle.Error as e:
            error, = e.args
            self.logger.error(f"✗ Oracle connection error: {error.message}")
            raise
    
    def create_tables(self):
        """Create all required tables"""
        cursor = self.connection.cursor()
        
        # 1. TEST_RUNS table
        try:
            cursor.execute('''
                CREATE TABLE TEST_RUNS (
                    TEST_RUN_ID VARCHAR2(100) PRIMARY KEY,
                    TEST_NAME VARCHAR2(200),
                    START_TIME TIMESTAMP,
                    END_TIME TIMESTAMP,
                    DURATION_MINUTES NUMBER,
                    STATUS VARCHAR2(50),
                    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IDX_TEST_RUN_START ON TEST_RUNS(START_TIME)')
            self.logger.info("✓ Created TEST_RUNS table")
        except cx_Oracle.DatabaseError as e:
            if 'ORA-00955' not in str(e):
                raise
        
        # 2. APPD_SERVER_METRICS table
        try:
            cursor.execute('''
                CREATE TABLE APPD_SERVER_METRICS (
                    ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    TEST_RUN_ID VARCHAR2(100) NOT NULL,
                    APP_NAME VARCHAR2(100),
                    TIER_NAME VARCHAR2(100),
                    NODE_NAME VARCHAR2(100),
                    METRIC_NAME VARCHAR2(200),
                    METRIC_VALUE BINARY_DOUBLE,
                    TIMESTAMP NUMBER(19),
                    COLLECTED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT FK_APPD_SERVER_TEST_RUN FOREIGN KEY (TEST_RUN_ID) 
                        REFERENCES TEST_RUNS(TEST_RUN_ID)
                )
            ''')
            cursor.execute('CREATE INDEX IDX_APPD_SERVER_TEST_RUN ON APPD_SERVER_METRICS(TEST_RUN_ID)')
            cursor.execute('CREATE INDEX IDX_APPD_SERVER_NODE ON APPD_SERVER_METRICS(NODE_NAME)')
            self.logger.info("✓ Created APPD_SERVER_METRICS table")
        except cx_Oracle.DatabaseError as e:
            if 'ORA-00955' not in str(e):
                raise
        
        # 3. APPD_JVM_METRICS table
        try:
            cursor.execute('''
                CREATE TABLE APPD_JVM_METRICS (
                    ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    TEST_RUN_ID VARCHAR2(100) NOT NULL,
                    APP_NAME VARCHAR2(100),
                    TIER_NAME VARCHAR2(100),
                    NODE_NAME VARCHAR2(100),
                    METRIC_NAME VARCHAR2(200),
                    METRIC_VALUE BINARY_DOUBLE,
                    TIMESTAMP NUMBER(19),
                    COLLECTED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT FK_APPD_JVM_TEST_RUN FOREIGN KEY (TEST_RUN_ID) 
                        REFERENCES TEST_RUNS(TEST_RUN_ID)
                )
            ''')
            cursor.execute('CREATE INDEX IDX_APPD_JVM_TEST_RUN ON APPD_JVM_METRICS(TEST_RUN_ID)')
            cursor.execute('CREATE INDEX IDX_APPD_JVM_NODE ON APPD_JVM_METRICS(NODE_NAME)')
            self.logger.info("✓ Created APPD_JVM_METRICS table")
        except cx_Oracle.DatabaseError as e:
            if 'ORA-00955' not in str(e):
                raise
        
        # 4. APPD_APPLICATION_METRICS table
        try:
            cursor.execute('''
                CREATE TABLE APPD_APPLICATION_METRICS (
                    ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    TEST_RUN_ID VARCHAR2(100) NOT NULL,
                    APP_NAME VARCHAR2(100),
                    TIER_NAME VARCHAR2(100),
                    METRIC_NAME VARCHAR2(200),
                    METRIC_VALUE BINARY_DOUBLE,
                    TIMESTAMP NUMBER(19),
                    COLLECTED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT FK_APPD_APP_TEST_RUN FOREIGN KEY (TEST_RUN_ID) 
                        REFERENCES TEST_RUNS(TEST_RUN_ID)
                )
            ''')
            cursor.execute('CREATE INDEX IDX_APPD_APP_TEST_RUN ON APPD_APPLICATION_METRICS(TEST_RUN_ID)')
            cursor.execute('CREATE INDEX IDX_APPD_APP_TIER ON APPD_APPLICATION_METRICS(TIER_NAME)')
            self.logger.info("✓ Created APPD_APPLICATION_METRICS table")
        except cx_Oracle.DatabaseError as e:
            if 'ORA-00955' not in str(e):
                raise
        
        # 5. KIBANA_API_METRICS table
        try:
            cursor.execute('''
                CREATE TABLE KIBANA_API_METRICS (
                    ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    TEST_RUN_ID VARCHAR2(100) NOT NULL,
                    DASHBOARD_NAME VARCHAR2(200),
                    API_NAME VARCHAR2(500),
                    TOTAL_COUNT NUMBER,
                    PASS_COUNT NUMBER,
                    FAIL_COUNT NUMBER,
                    P90_RESPONSE_TIME BINARY_DOUBLE,
                    P95_RESPONSE_TIME BINARY_DOUBLE,
                    AVG_RESPONSE_TIME BINARY_DOUBLE,
                    MIN_RESPONSE_TIME BINARY_DOUBLE,
                    MAX_RESPONSE_TIME BINARY_DOUBLE,
                    COLLECTED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT FK_KIBANA_TEST_RUN FOREIGN KEY (TEST_RUN_ID) 
                        REFERENCES TEST_RUNS(TEST_RUN_ID)
                )
            ''')
            cursor.execute('CREATE INDEX IDX_KIBANA_TEST_RUN ON KIBANA_API_METRICS(TEST_RUN_ID)')
            cursor.execute('CREATE INDEX IDX_KIBANA_API_NAME ON KIBANA_API_METRICS(API_NAME)')
            self.logger.info("✓ Created KIBANA_API_METRICS table")
        except cx_Oracle.DatabaseError as e:
            if 'ORA-00955' not in str(e):
                raise
        
        self.connection.commit()
        self.logger.info("✓ All tables verified/created")
    
    def insert_test_run(self, test_run_id: str, test_name: str = None, 
                       start_time: datetime = None, duration_minutes: int = None):
        """Insert new test run"""
        cursor = self.connection.cursor()
        
        if start_time is None:
            start_time = datetime.now()
        
        try:
            cursor.execute('''
                INSERT INTO TEST_RUNS (TEST_RUN_ID, TEST_NAME, START_TIME, DURATION_MINUTES, STATUS)
                VALUES (:1, :2, :3, :4, :5)
            ''', (test_run_id, test_name, start_time, duration_minutes, 'running'))
            
            self.connection.commit()
            self.logger.info(f"✓ Test run created: {test_run_id}")
        except Exception as e:
            self.logger.error(f"✗ Error inserting test run: {e}")
            self.connection.rollback()
    
    def update_test_run_status(self, test_run_id: str, status: str, end_time: datetime = None):
        """Update test run status"""
        cursor = self.connection.cursor()
        
        if end_time is None:
            end_time = datetime.now()
        
        try:
            cursor.execute('''
                UPDATE TEST_RUNS 
                SET STATUS = :1, END_TIME = :2
                WHERE TEST_RUN_ID = :3
            ''', (status, end_time, test_run_id))
            
            self.connection.commit()
            self.logger.info(f"✓ Test run updated: {test_run_id} - {status}")
        except Exception as e:
            self.logger.error(f"✗ Error updating test run: {e}")
            self.connection.rollback()
    
    def insert_appd_server_metrics(self, test_run_id: str, metrics_data: Dict):
        """Insert AppDynamics server metrics"""
        cursor = self.connection.cursor()
        inserted = 0
        
        try:
            for app_name, app_data in metrics_data.items():
                for tier_name, tier_data in app_data.items():
                    nodes = tier_data.get('nodes', {})
                    
                    for node_name, node_data in nodes.items():
                        server_metrics = node_data.get('server_metrics', {})
                        
                        for metric_name, values in server_metrics.items():
                            for value_point in values:
                                cursor.execute('''
                                    INSERT INTO APPD_SERVER_METRICS 
                                    (TEST_RUN_ID, APP_NAME, TIER_NAME, NODE_NAME, 
                                     METRIC_NAME, METRIC_VALUE, TIMESTAMP)
                                    VALUES (:1, :2, :3, :4, :5, :6, :7)
                                ''', (
                                    test_run_id, app_name, tier_name, node_name,
                                    metric_name, value_point.get('value'),
                                    value_point.get('timestamp')
                                ))
                                inserted += 1
            
            self.connection.commit()
            self.logger.info(f"✓ Inserted {inserted} server metric records")
        except Exception as e:
            self.logger.error(f"✗ Error inserting server metrics: {e}")
            self.connection.rollback()
    
    def insert_appd_jvm_metrics(self, test_run_id: str, metrics_data: Dict):
        """Insert AppDynamics JVM metrics"""
        cursor = self.connection.cursor()
        inserted = 0
        
        try:
            for app_name, app_data in metrics_data.items():
                for tier_name, tier_data in app_data.items():
                    nodes = tier_data.get('nodes', {})
                    
                    for node_name, node_data in nodes.items():
                        jvm_metrics = node_data.get('jvm_metrics', {})
                        
                        for metric_name, values in jvm_metrics.items():
                            for value_point in values:
                                cursor.execute('''
                                    INSERT INTO APPD_JVM_METRICS 
                                    (TEST_RUN_ID, APP_NAME, TIER_NAME, NODE_NAME, 
                                     METRIC_NAME, METRIC_VALUE, TIMESTAMP)
                                    VALUES (:1, :2, :3, :4, :5, :6, :7)
                                ''', (
                                    test_run_id, app_name, tier_name, node_name,
                                    metric_name, value_point.get('value'),
                                    value_point.get('timestamp')
                                ))
                                inserted += 1
            
            self.connection.commit()
            self.logger.info(f"✓ Inserted {inserted} JVM metric records")
        except Exception as e:
            self.logger.error(f"✗ Error inserting JVM metrics: {e}")
            self.connection.rollback()
    
    def insert_appd_application_metrics(self, test_run_id: str, metrics_data: Dict):
        """Insert AppDynamics application metrics"""
        cursor = self.connection.cursor()
        inserted = 0
        
        try:
            for app_name, app_data in metrics_data.items():
                for tier_name, tier_data in app_data.items():
                    app_metrics = tier_data.get('application_metrics', {})
                    
                    for metric_name, values in app_metrics.items():
                        for value_point in values:
                            cursor.execute('''
                                INSERT INTO APPD_APPLICATION_METRICS 
                                (TEST_RUN_ID, APP_NAME, TIER_NAME, 
                                 METRIC_NAME, METRIC_VALUE, TIMESTAMP)
                                VALUES (:1, :2, :3, :4, :5, :6)
                            ''', (
                                test_run_id, app_name, tier_name,
                                metric_name, value_point.get('value'),
                                value_point.get('timestamp')
                            ))
                            inserted += 1
            
            self.connection.commit()
            self.logger.info(f"✓ Inserted {inserted} application metric records")
        except Exception as e:
            self.logger.error(f"✗ Error inserting application metrics: {e}")
            self.connection.rollback()
    
    def insert_kibana_api_metrics(self, test_run_id: str, metrics_data: Dict):
        """Insert Kibana API metrics"""
        cursor = self.connection.cursor()
        inserted = 0
        
        try:
            for dashboard_name, dashboard_data in metrics_data.items():
                apis = dashboard_data.get('apis', [])
                
                for api in apis:
                    cursor.execute('''
                        INSERT INTO KIBANA_API_METRICS 
                        (TEST_RUN_ID, DASHBOARD_NAME, API_NAME, 
                         TOTAL_COUNT, PASS_COUNT, FAIL_COUNT,
                         P90_RESPONSE_TIME, P95_RESPONSE_TIME,
                         AVG_RESPONSE_TIME, MIN_RESPONSE_TIME, MAX_RESPONSE_TIME)
                        VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11)
                    ''', (
                        test_run_id, dashboard_name, api.get('api_name'),
                        api.get('total_count'), api.get('pass_count'), api.get('fail_count'),
                        api.get('p90_response_time'), api.get('p95_response_time'),
                        api.get('avg_response_time'), api.get('min_response_time'),
                        api.get('max_response_time')
                    ))
                    inserted += 1
            
            self.connection.commit()
            self.logger.info(f"✓ Inserted {inserted} Kibana API metric records")
        except Exception as e:
            self.logger.error(f"✗ Error inserting Kibana metrics: {e}")
            self.connection.rollback()
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.logger.info("✓ Database connection closed")