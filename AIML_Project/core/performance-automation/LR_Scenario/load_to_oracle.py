#!/usr/bin/env python3
"""
Oracle Database Loader for Performance Center Results
Inserts parsed transaction data into Oracle database
"""

import sys
import json
import argparse
from datetime import datetime
import cx_Oracle

class OracleLoader:
    def __init__(self, username, password, dsn, test_run_info=None):
        """
        Initialize Oracle connection
        
        Args:
            username: Oracle username
            password: Oracle password
            dsn: Oracle DSN (host:port/service_name)
            test_run_info: Dict with test_id, run_id, build_number, etc.
        """
        self.username = username
        self.password = password
        self.dsn = dsn
        self.connection = None
        self.test_run_info = test_run_info or {}
        
    def connect(self):
        """Establish Oracle connection"""
        try:
            print(f"Connecting to Oracle: {self.dsn}")
            self.connection = cx_Oracle.connect(
                user=self.username,
                password=self.password,
                dsn=self.dsn
            )
            print("✓ Connected to Oracle successfully")
            return True
        except cx_Oracle.Error as error:
            print(f"✗ Oracle connection failed: {error}")
            return False
    
    def disconnect(self):
        """Close Oracle connection"""
        if self.connection:
            self.connection.close()
            print("✓ Disconnected from Oracle")
    
    def create_tables_if_not_exist(self):
        """Create tables if they don't exist"""
        cursor = self.connection.cursor()
        
        # Create test runs table
        create_runs_table = """
        CREATE TABLE IF NOT EXISTS PC_TEST_RUNS (
            RUN_ID NUMBER PRIMARY KEY,
            TEST_ID NUMBER NOT NULL,
            TEST_NAME VARCHAR2(255),
            BUILD_NUMBER VARCHAR2(50),
            RUN_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            TEST_STATUS VARCHAR2(50),
            TEST_DURATION NUMBER,
            PC_HOST VARCHAR2(255),
            PC_PROJECT VARCHAR2(255),
            CREATED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Create transactions table
        create_transactions_table = """
        CREATE TABLE IF NOT EXISTS PC_TRANSACTIONS (
            TRANSACTION_ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            RUN_ID NUMBER NOT NULL,
            TRANSACTION_NAME VARCHAR2(255) NOT NULL,
            AVG_RESPONSE_TIME NUMBER(10,2),
            MIN_RESPONSE_TIME NUMBER(10,2),
            MAX_RESPONSE_TIME NUMBER(10,2),
            PERCENTILE_90 NUMBER(10,2),
            PERCENTILE_95 NUMBER(10,2),
            ERROR_RATE NUMBER(5,2),
            TRANSACTION_COUNT NUMBER,
            CREATED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT FK_RUN FOREIGN KEY (RUN_ID) REFERENCES PC_TEST_RUNS(RUN_ID)
        )
        """
        
        try:
            # Try to create tables (Oracle 12c+ supports IF NOT EXISTS)
            cursor.execute(create_runs_table)
            cursor.execute(create_transactions_table)
            self.connection.commit()
            print("✓ Tables verified/created")
        except cx_Oracle.Error as e:
            # Tables might already exist, that's okay
            if "ORA-00955" in str(e):  # Name already used
                print("✓ Tables already exist")
            else:
                # For Oracle < 12c, try without IF NOT EXISTS
                self._create_tables_legacy(cursor)
        
        cursor.close()
    
    def _create_tables_legacy(self, cursor):
        """Create tables for older Oracle versions"""
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) FROM user_tables WHERE table_name = 'PC_TEST_RUNS'
        """)
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                CREATE TABLE PC_TEST_RUNS (
                    RUN_ID NUMBER PRIMARY KEY,
                    TEST_ID NUMBER NOT NULL,
                    TEST_NAME VARCHAR2(255),
                    BUILD_NUMBER VARCHAR2(50),
                    RUN_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    TEST_STATUS VARCHAR2(50),
                    TEST_DURATION NUMBER,
                    PC_HOST VARCHAR2(255),
                    PC_PROJECT VARCHAR2(255),
                    CREATED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✓ Created PC_TEST_RUNS table")
        
        cursor.execute("""
            SELECT COUNT(*) FROM user_tables WHERE table_name = 'PC_TRANSACTIONS'
        """)
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                CREATE TABLE PC_TRANSACTIONS (
                    TRANSACTION_ID NUMBER PRIMARY KEY,
                    RUN_ID NUMBER NOT NULL,
                    TRANSACTION_NAME VARCHAR2(255) NOT NULL,
                    AVG_RESPONSE_TIME NUMBER(10,2),
                    MIN_RESPONSE_TIME NUMBER(10,2),
                    MAX_RESPONSE_TIME NUMBER(10,2),
                    PERCENTILE_90 NUMBER(10,2),
                    PERCENTILE_95 NUMBER(10,2),
                    ERROR_RATE NUMBER(5,2),
                    TRANSACTION_COUNT NUMBER,
                    CREATED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create sequence for transaction ID
            cursor.execute("""
                CREATE SEQUENCE PC_TRANSACTIONS_SEQ START WITH 1 INCREMENT BY 1
            """)
            
            print("✓ Created PC_TRANSACTIONS table and sequence")
        
        self.connection.commit()
    
    def insert_test_run(self):
        """Insert test run metadata"""
        cursor = self.connection.cursor()
        
        insert_sql = """
            INSERT INTO PC_TEST_RUNS (
                RUN_ID, TEST_ID, TEST_NAME, BUILD_NUMBER, RUN_DATE, TEST_STATUS,
                TEST_DURATION, PC_HOST, PC_PROJECT
            ) VALUES (
                :run_id, :test_id, :test_name, :build_number, :run_date, :test_status,
                :test_duration, :pc_host, :pc_project
            )
        """
        
        run_data = {
            'run_id': self.test_run_info.get('run_id'),
            'test_id': self.test_run_info.get('test_id'),
            'test_name': self.test_run_info.get('test_name'),
            'build_number': self.test_run_info.get('build_number'),
            'run_date': self.test_run_info.get('run_date', datetime.now()),
            'test_status': self.test_run_info.get('test_status'),
            'test_duration': self.test_run_info.get('test_duration'),
            'pc_host': self.test_run_info.get('pc_host'),
            'pc_project': self.test_run_info.get('pc_project')
        }
        
        try:
            cursor.execute(insert_sql, run_data)
            self.connection.commit()
            print(f"✓ Inserted test run: {run_data['run_id']}")
            return True
        except cx_Oracle.IntegrityError:
            # Run ID already exists, update instead
            print(f"Run ID {run_data['run_id']} already exists, skipping...")
            return True
        except cx_Oracle.Error as error:
            print(f"✗ Failed to insert test run: {error}")
            return False
        finally:
            cursor.close()
    
    def insert_transactions(self, transactions):
        """Insert transaction data"""
        if not transactions:
            print("No transactions to insert")
            return False
        
        cursor = self.connection.cursor()
        
        # Try with identity column first (Oracle 12c+)
        insert_sql = """
            INSERT INTO PC_TRANSACTIONS (
                RUN_ID, TRANSACTION_NAME, AVG_RESPONSE_TIME, MIN_RESPONSE_TIME,
                MAX_RESPONSE_TIME, PERCENTILE_90, PERCENTILE_95, ERROR_RATE,
                TRANSACTION_COUNT
            ) VALUES (
                :run_id, :transaction_name, :avg_response_time, :min_response_time,
                :max_response_time, :percentile_90, :percentile_95, :error_rate,
                :transaction_count
            )
        """
        
        run_id = self.test_run_info.get('run_id')
        inserted_count = 0
        
        for txn in transactions:
            txn_data = {
                'run_id': run_id,
                'transaction_name': txn.get('transaction_name'),
                'avg_response_time': txn.get('avg_response_time'),
                'min_response_time': txn.get('min_response_time'),
                'max_response_time': txn.get('max_response_time'),
                'percentile_90': txn.get('percentile_90'),
                'percentile_95': txn.get('percentile_95'),
                'error_rate': txn.get('error_rate'),
                'transaction_count': txn.get('transaction_count')
            }
            
            try:
                cursor.execute(insert_sql, txn_data)
                inserted_count += 1
            except cx_Oracle.Error as error:
                print(f"✗ Failed to insert transaction '{txn_data['transaction_name']}': {error}")
        
        self.connection.commit()
        cursor.close()
        
        print(f"✓ Inserted {inserted_count} transactions")
        return inserted_count > 0
    
    def load_from_json(self, json_file):
        """Load data from JSON file and insert into database"""
        print(f"Loading data from: {json_file}")
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        transactions = data.get('transactions', [])
        print(f"Found {len(transactions)} transactions in JSON")
        
        # Insert test run
        if self.test_run_info.get('run_id'):
            self.insert_test_run()
        
        # Insert transactions
        return self.insert_transactions(transactions)

def main():
    parser = argparse.ArgumentParser(description='Load PC transaction data into Oracle')
    parser.add_argument('--json-file', required=True, help='JSON file with transaction data')
    parser.add_argument('--oracle-user', required=True, help='Oracle username')
    parser.add_argument('--oracle-password', required=True, help='Oracle password')
    parser.add_argument('--oracle-dsn', required=True, help='Oracle DSN (host:port/service)')
    parser.add_argument('--run-id', type=int, required=True, help='Test run ID')
    parser.add_argument('--test-id', type=int, help='Test ID')
    parser.add_argument('--test-name', help='Test name')
    parser.add_argument('--build-number', help='Jenkins build number')
    parser.add_argument('--test-status', help='Test status')
    parser.add_argument('--test-duration', type=int, help='Test duration in seconds')
    parser.add_argument('--pc-host', help='PC host')
    parser.add_argument('--pc-project', help='PC project name')
    parser.add_argument('--create-tables', action='store_true', help='Create tables if not exist')
    
    args = parser.parse_args()
    
    # Prepare test run info
    test_run_info = {
        'run_id': args.run_id,
        'test_id': args.test_id,
        'test_name': args.test_name,
        'build_number': args.build_number,
        'test_status': args.test_status,
        'test_duration': args.test_duration,
        'pc_host': args.pc_host,
        'pc_project': args.pc_project,
        'run_date': datetime.now()
    }
    
    # Create loader
    loader = OracleLoader(
        username=args.oracle_user,
        password=args.oracle_password,
        dsn=args.oracle_dsn,
        test_run_info=test_run_info
    )
    
    # Connect
    if not loader.connect():
        sys.exit(1)
    
    try:
        # Create tables if requested
        if args.create_tables:
            loader.create_tables_if_not_exist()
        
        # Load data
        success = loader.load_from_json(args.json_file)
        
        if success:
            print("\n✓ Data loaded successfully!")
            sys.exit(0)
        else:
            print("\n✗ Data loading failed")
            sys.exit(1)
    
    finally:
        loader.disconnect()

if __name__ == "__main__":
    main()
