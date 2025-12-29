from flask import Flask, render_template, request, jsonify
import cx_Oracle
import re
from datetime import datetime

app = Flask(__name__)

# CONFIGURE YOUR DATABASES HERE
PROD_DB_CONFIG = {
    'user': 'prod_user',
    'password': 'prod_password',
    'dsn': 'localhost:1521/PRODDB'
}

PTE_DB_CONFIG = {
    'user': 'pte_user',
    'password': 'pte_password',
    'dsn': 'localhost:1521/PTEDB'
}

class NLQueryProcessor:
    """Process natural language queries and convert to SQL"""
    
    def __init__(self):
        # Define query patterns and their SQL templates
        self.patterns = {
            'payment_count_branch_peak': {
                'regex': r'(?:how many|count|total).*payment.*branch\s+(\d+).*(?:peak|busy)',
                'prod_query': """
                    SELECT b.branch_id, 
                           TO_CHAR(t.timestamp, 'HH24:MI') || '-' || 
                           TO_CHAR(t.timestamp + INTERVAL '1' HOUR, 'HH24:MI') as hour_range,
                           COUNT(*) as payment_count,
                           ROUND(SUM(CASE WHEN t.status = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
                    FROM PROD_STATS.TRANSACTIONS t
                    JOIN PROD_STATS.BRANCH_STATS b ON t.branch_id = b.branch_id
                    WHERE t.branch_id = {branch_id}
                      AND TO_CHAR(t.timestamp, 'HH24') BETWEEN '09' AND '14'
                      AND t.txn_type = 'PAYMENT'
                      AND t.timestamp >= TRUNC(SYSDATE) - 1
                    GROUP BY b.branch_id, TO_CHAR(t.timestamp, 'HH24:MI')
                    ORDER BY payment_count DESC
                """,
                'pte_query': """
                    SELECT test_case,
                           expected_count,
                           actual_count,
                           status,
                           ROUND((actual_count - expected_count) * 100.0 / expected_count, 2) as variance_pct
                    FROM PTE_METRICS.TEST_RESULTS
                    WHERE branch_id = {branch_id}
                      AND test_case LIKE '%PEAK%'
                      AND timestamp >= TRUNC(SYSDATE) - 7
                    ORDER BY timestamp DESC
                    FETCH FIRST 10 ROWS ONLY
                """
            },
            'transaction_volume': {
                'regex': r'(?:show|display|get).*(?:transaction|txn).*volume.*(?:last|past)\s+(\d+)\s+day',
                'prod_query': """
                    SELECT TRUNC(timestamp) as date,
                           COUNT(*) as total_transactions,
                           SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                           SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                           ROUND(AVG(amount), 2) as avg_amount
                    FROM PROD_STATS.TRANSACTIONS
                    WHERE timestamp >= TRUNC(SYSDATE) - {days}
                    GROUP BY TRUNC(timestamp)
                    ORDER BY date DESC
                """,
                'pte_query': """
                    SELECT TRUNC(timestamp) as test_date,
                           test_case,
                           AVG(throughput) as avg_throughput,
                           AVG(response_time) as avg_response_time,
                           AVG(success_rate) as avg_success_rate
                    FROM PTE_METRICS.PERFORMANCE_METRICS
                    WHERE timestamp >= TRUNC(SYSDATE) - {days}
                    GROUP BY TRUNC(timestamp), test_case
                    ORDER BY test_date DESC
                """
            },
            'compare_pte_prod': {
                'regex': r'compar.*(?:pte|test).*(?:prod|production).*(?:batch|process)',
                'prod_query': """
                    SELECT 'PRODUCTION' as source,
                           COUNT(*) as total_txns,
                           ROUND(AVG(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) * 100, 2) as success_rate,
                           ROUND(AVG(EXTRACT(SECOND FROM (updated_at - timestamp))), 2) as avg_response_time
                    FROM PROD_STATS.TRANSACTIONS
                    WHERE txn_type = 'BATCH'
                      AND timestamp >= TRUNC(SYSDATE) - 7
                """,
                'pte_query': """
                    SELECT metric_name,
                           AVG(prod_value) as prod_avg,
                           AVG(pte_value) as pte_avg,
                           ROUND(AVG(variance), 2) as avg_variance
                    FROM PTE_METRICS.COMPARISON_LOG
                    WHERE metric_name LIKE '%BATCH%'
                      AND timestamp >= TRUNC(SYSDATE) - 7
                    GROUP BY metric_name
                """
            },
            'success_rate_branch': {
                'regex': r'(?:what|show).*success rate.*branch\s+(\d+).*(?:yesterday|last day)',
                'prod_query': """
                    SELECT branch_id,
                           COUNT(*) as total_txns,
                           SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                           ROUND(SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate,
                           ROUND(AVG(amount), 2) as avg_amount
                    FROM PROD_STATS.TRANSACTIONS
                    WHERE branch_id = {branch_id}
                      AND timestamp >= TRUNC(SYSDATE) - 1
                      AND timestamp < TRUNC(SYSDATE)
                    GROUP BY branch_id
                """,
                'pte_query': """
                    SELECT test_case,
                           success_rate as expected_rate,
                           status
                    FROM PTE_METRICS.PERFORMANCE_METRICS
                    WHERE test_case LIKE '%BR_{branch_id}%'
                    ORDER BY timestamp DESC
                    FETCH FIRST 5 ROWS ONLY
                """
            },
            'failed_transactions': {
                'regex': r'(?:show|get|display).*failed.*transaction.*(?:error code|last hour)',
                'prod_query': """
                    SELECT error_code,
                           COUNT(*) as occurrence_count,
                           MIN(timestamp) as first_occurrence,
                           MAX(timestamp) as last_occurrence,
                           LISTAGG(DISTINCT txn_type, ', ') WITHIN GROUP (ORDER BY txn_type) as affected_types
                    FROM PROD_STATS.TRANSACTIONS
                    WHERE status = 'FAILED'
                      AND timestamp >= SYSDATE - INTERVAL '1' HOUR
                    GROUP BY error_code
                    ORDER BY occurrence_count DESC
                """,
                'pte_query': """
                    SELECT test_case,
                           expected_count,
                           actual_count,
                           status
                    FROM PTE_METRICS.TEST_RESULTS
                    WHERE test_case LIKE '%FAIL%' OR test_case LIKE '%ERROR%'
                    ORDER BY timestamp DESC
                    FETCH FIRST 10 ROWS ONLY
                """
            }
        }
    
    def parse_query(self, query):
        """Parse natural language query and extract parameters"""
        query_lower = query.lower()
        
        for pattern_name, pattern_data in self.patterns.items():
            match = re.search(pattern_data['regex'], query_lower, re.IGNORECASE)
            if match:
                params = {}
                groups = match.groups()
                
                # Extract parameters based on pattern
                if 'branch' in pattern_name and groups:
                    params['branch_id'] = groups[0]
                elif 'volume' in pattern_name and groups:
                    params['days'] = groups[0]
                
                return {
                    'pattern': pattern_name,
                    'prod_query': pattern_data['prod_query'].format(**params) if params else pattern_data['prod_query'],
                    'pte_query': pattern_data['pte_query'].format(**params) if params else pattern_data['pte_query'],
                    'params': params
                }
        
        return None

class DatabaseExecutor:
    """Execute SQL queries on Oracle databases"""
    
    @staticmethod
    def execute_query(query, db_config):
        """Execute a query and return results"""
        try:
            connection = cx_Oracle.connect(
                user=db_config['user'],
                password=db_config['password'],
                dsn=db_config['dsn']
            )
            cursor = connection.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch all rows
            rows = cursor.fetchall()
            
            # Convert to list of dicts for JSON serialization
            results = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Handle date/datetime objects
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[col] = value
                results.append(row_dict)
            
            cursor.close()
            connection.close()
            
            return {
                'columns': columns,
                'rows': results,
                'row_count': len(results)
            }
        except cx_Oracle.Error as error:
            return {
                'error': str(error),
                'columns': [],
                'rows': [],
                'row_count': 0
            }

# Initialize processor
query_processor = NLQueryProcessor()
db_executor = DatabaseExecutor()

@app.route('/')
def index():
    """Render the main interface"""
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process natural language query and return results"""
    data = request.json
    nl_query = data.get('query', '')
    
    if not nl_query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Parse the natural language query
    parsed = query_processor.parse_query(nl_query)
    
    if not parsed:
        return jsonify({
            'error': 'Could not understand the query. Please try rephrasing or use one of the sample queries.'
        }), 400
    
    # Execute queries on both databases
    prod_results = db_executor.execute_query(parsed['prod_query'], PROD_DB_CONFIG)
    pte_results = db_executor.execute_query(parsed['pte_query'], PTE_DB_CONFIG)
    
    return jsonify({
        'pattern': parsed['pattern'],
        'prod_query': parsed['prod_query'],
        'pte_query': parsed['pte_query'],
        'prod_results': prod_results,
        'pte_results': pte_results,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/sample-queries', methods=['GET'])
def get_sample_queries():
    """Return sample queries"""
    samples = [
        "How many payments initiated for branch 600 at peak hour?",
        "Show transaction volume for last 7 days",
        "Compare PTE metrics with production for batch processing",
        "What is the success rate for branch 450 yesterday?",
        "Show failed transactions by error code in the last hour"
    ]
    return jsonify({'samples': samples})

if __name__ == '__main__':
    print("=" * 60)
    print("Natural Language Query Interface Server")
    print("=" * 60)
    print("\nStarting server on http://localhost:5000")
    print("\nMake sure to update database credentials in the code:")
    print("  - PROD_DB_CONFIG")
    print("  - PTE_DB_CONFIG")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    