        stage('Load to Oracle Database') {
            when {
                expression { params.LOAD_TO_ORACLE }
            }
            steps {
                script {
                    echo ""
                    echo "=" * 60
                    echo "Loading Data to Oracle"
                    echo "=" * 60
                    
                    def runId = sh(script: "cat ${WORKSPACE}/results/run_id.txt", returnStdout: true).trim()
                    def resultId = sh(script: "cat ${WORKSPACE}/results/result_id.txt 2>/dev/null || echo ''", returnStdout: true).trim()
                    def finalStatus = sh(script: "cat ${WORKSPACE}/results/final_status.txt 2>/dev/null || echo 'UNKNOWN'", returnStdout: true).trim()
                    def scenarioName = sh(script: "cat ${WORKSPACE}/results/scenario_name.txt 2>/dev/null || echo 'Unknown'", returnStdout: true).trim()
                    
                    echo "Run ID: ${runId}"
                    echo "Scenario Name: ${scenarioName}"
                    echo "Status: ${finalStatus}"
                    
                    // Install cx_Oracle if not present
                    sh """
                        pip3 install --user cx_Oracle --break-system-packages 2>/dev/null || \
                        pip3 install --user cx_Oracle || \
                        echo "cx_Oracle may already be installed"
                    """
                    
                    // Create inline Oracle loader script
                    sh """
cat > ${WORKSPACE}/scripts/load_oracle.py << 'PYEOF'
#!/usr/bin/env python3
import sys
import json
import cx_Oracle
from datetime import datetime

def load_to_oracle(oracle_dsn, oracle_user, oracle_pass, json_file, run_info):
    # Connect
    print(f"Connecting to Oracle: {oracle_dsn}")
    conn = cx_Oracle.connect(oracle_user, oracle_pass, oracle_dsn)
    cursor = conn.cursor()
    print("✓ Connected to Oracle")
    
    # Read JSON
    with open(json_file) as f:
        data = json.load(f)
    
    # Insert test run with scenario name
    try:
        cursor.execute('''
            INSERT INTO PC_TEST_RUNS 
            (RUN_ID, TEST_ID, SCENARIO_NAME, BUILD_NUMBER, TEST_STATUS, 
             TEST_DURATION, PC_HOST, PC_PROJECT, RUN_DATE)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, SYSDATE)
        ''', (
            int(run_info['run_id']),
            int(run_info['test_id']),
            run_info['scenario_name'],
            run_info['build_number'],
            run_info['status'],
            int(run_info['duration']),
            run_info['pc_host'],
            run_info['pc_project']
        ))
        print(f"✓ Inserted run {run_info['run_id']} - Scenario: {run_info['scenario_name']}")
    except cx_Oracle.IntegrityError:
        print(f"Run {run_info['run_id']} already exists, updating scenario name...")
        cursor.execute('''
            UPDATE PC_TEST_RUNS 
            SET SCENARIO_NAME = :1, TEST_STATUS = :2
            WHERE RUN_ID = :3
        ''', (run_info['scenario_name'], run_info['status'], int(run_info['run_id'])))
    
    # Insert transactions
    count = 0
    for txn in data['transactions']:
        try:
            cursor.execute('''
                INSERT INTO PC_TRANSACTIONS 
                (RUN_ID, TRANSACTION_NAME, AVG_RESPONSE_TIME, MIN_RESPONSE_TIME, 
                 MAX_RESPONSE_TIME, PERCENTILE_90, PERCENTILE_95, ERROR_RATE, TRANSACTION_COUNT)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
            ''', (
                int(run_info['run_id']),
                txn['transaction_name'],
                txn.get('avg_response_time'),
                txn.get('min_response_time'),
                txn.get('max_response_time'),
                txn.get('percentile_90'),
                txn.get('percentile_95'),
                txn.get('error_rate'),
                txn.get('transaction_count')
            ))
            count += 1
        except Exception as e:
            print(f"Error inserting {txn['transaction_name']}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✓ Loaded {count} transactions to Oracle")
    return count

if __name__ == '__main__':
    oracle_dsn = sys.argv[1]
    oracle_user = sys.argv[2]
    oracle_pass = sys.argv[3]
    json_file = sys.argv[4]
    run_id = sys.argv[5]
    test_id = sys.argv[6]
    scenario_name = sys.argv[7]
    build_num = sys.argv[8]
    status = sys.argv[9]
    duration = sys.argv[10]
    pc_host = sys.argv[11]
    pc_project = sys.argv[12]
    
    run_info = {
        'run_id': run_id,
        'test_id': test_id,
        'scenario_name': scenario_name,
        'build_number': build_num,
        'status': status,
        'duration': duration,
        'pc_host': pc_host,
        'pc_project': pc_project
    }
    
    count = load_to_oracle(oracle_dsn, oracle_user, oracle_pass, json_file, run_info)
    sys.exit(0 if count > 0 else 1)
PYEOF

chmod +x ${WORKSPACE}/scripts/load_oracle.py
"""
                    
                    // Load to Oracle with credentials
                    withCredentials([usernamePassword(
                        credentialsId: 'oracle-credentials',
                        usernameVariable: 'ORACLE_USER',
                        passwordVariable: 'ORACLE_PASS'
                    )]) {
                        
                        def oracleDSN = "${params.ORACLE_HOST}:${params.ORACLE_PORT}/${params.ORACLE_SERVICE}"
                        
                        echo "Oracle DSN: ${oracleDSN}"
                        echo "Loading data for Scenario: ${scenarioName}"
                        
                        sh """
                            python3 ${WORKSPACE}/scripts/load_oracle.py \
                            "${oracleDSN}" \
                            "${ORACLE_USER}" \
                            "${ORACLE_PASS}" \
                            "${WORKSPACE}/results/transactions_data.json" \
                            "${runId}" \
                            "${params.TEST_ID}" \
                            "${scenarioName}" \
                            "${BUILD_NUMBER}" \
                            "${finalStatus}" \
                            "${params.TEST_DURATION}" \
                            "${params.PC_HOST}" \
                            "${params.PC_PROJECT}"
                        """
                    }
                    
                    echo ""
                    echo "✓ Data loaded to Oracle successfully"
                    echo "  - Run ID: ${runId}"
                    echo "  - Scenario: ${scenarioName}"
                    echo "  - Transactions loaded"
                }
            }
        }
