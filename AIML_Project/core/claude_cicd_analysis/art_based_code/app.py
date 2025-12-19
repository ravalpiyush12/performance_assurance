import cx_Oracle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__, static_folder='.')
CORS(app)

# Oracle DB Configuration
DB_CONFIG = {
    'user': 'your_username',
    'password': 'your_password',
    'dsn': 'your_host:1521/your_service_name'
}

class CICDAnalyzer:
    def __init__(self):
        self.connection = None
        self.df = None
        
    def connect_db(self):
        """Connect to Oracle Database"""
        try:
            self.connection = cx_Oracle.connect(**DB_CONFIG)
            print("✓ Connected to Oracle Database")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {str(e)}")
            return False
    
    def fetch_test_results(self, days=30):
        """
        Fetch test results from PTE table
        
        LOGIC: Retrieves all test data for the specified number of days
        EXAMPLE: days=7 fetches data from last 7 days
        """
        query = """
        SELECT 
            ART,
            API,
            PASS_COUNT,
            FAILURES,
            P95_RESPONSE_TIME,
            TEST_DATE,
            EXECUTION_TIME
        FROM PTE_TABLE
        WHERE TEST_DATE >= SYSDATE - :days
        ORDER BY TEST_DATE DESC
        """
        
        try:
            self.df = pd.read_sql(query, self.connection, params={'days': days})
            self.df['TEST_DATE'] = pd.to_datetime(self.df['TEST_DATE'])
            self.df['TOTAL_TESTS'] = self.df['PASS_COUNT'] + self.df['FAILURES']
            self.df['FAILURE_RATE'] = (self.df['FAILURES'] / self.df['TOTAL_TESTS'] * 100).round(2)
            self.df['SUCCESS_RATE'] = (self.df['PASS_COUNT'] / self.df['TOTAL_TESTS'] * 100).round(2)
            print(f"✓ Fetched {len(self.df)} records")
            return self.df
        except Exception as e:
            print(f"✗ Data fetch failed: {str(e)}")
            return None
    
    def calculate_daily_metrics(self):
        """
        Calculate daily aggregated metrics
        
        LOGIC: Groups data by date and aggregates metrics
        CALCULATION:
        - Sum all passes/failures per day
        - Average P95 response time per day
        - Calculate daily failure rate = (total failures / total tests) * 100
        
        EXAMPLE:
        Day 1: 500 passes, 50 failures → Failure Rate = (50/550)*100 = 9.09%
        """
        daily = self.df.groupby('TEST_DATE').agg({
            'PASS_COUNT': 'sum',
            'FAILURES': 'sum',
            'P95_RESPONSE_TIME': 'mean',
            'TOTAL_TESTS': 'sum'
        }).reset_index()
        
        daily['FAILURE_RATE'] = (daily['FAILURES'] / daily['TOTAL_TESTS'] * 100).round(2)
        daily['TEST_DATE'] = daily['TEST_DATE'].dt.strftime('%Y-%m-%d')
        return daily.to_dict('records')
    
    def predict_failure_rate(self, days_ahead=1):
        """
        Predict failure rate using Linear Regression
        
        LOGIC:
        1. Uses historical failure rates as training data
        2. Fits a linear model: y = mx + b where:
           - x = day number (0, 1, 2, ...)
           - y = failure rate
           - m = slope (trend direction)
           - b = intercept
        3. Predicts future values by extending the line
        
        CALCULATION EXAMPLE:
        Historical data:
        Day 0: 5% failure rate
        Day 1: 6% failure rate  
        Day 2: 7% failure rate
        Day 3: 8% failure rate
        
        Model learns: slope (m) = 1.0 (increasing 1% per day)
        Prediction for Day 4 = 8 + 1.0 = 9%
        Prediction for Day 5 = 9 + 1.0 = 10%
        
        TREND DETERMINATION:
        - slope > 0.1  → "increasing" (getting worse)
        - slope < -0.1 → "decreasing" (getting better)
        - else         → "stable"
        
        CONFIDENCE SCORE:
        R² score × 100 = how well the model fits data
        - 90-100% = very accurate prediction
        - 70-89%  = good prediction
        - <70%    = less reliable (data may be too random)
        
        MINIMUM DATA REQUIREMENT:
        Needs at least 3 data points to make prediction
        If less than 3 days of data, returns "Insufficient data"
        """
        daily = self.df.groupby('TEST_DATE').agg({
            'FAILURES': 'sum',
            'TOTAL_TESTS': 'sum'
        }).reset_index()
        
        if len(daily) < 3:
            return {
                'next_day_prediction': 0,
                'next_week_prediction': 0,
                'trend': 'insufficient_data',
                'confidence': 0,
                'message': 'Need at least 3 days of data for prediction'
            }
        
        daily['FAILURE_RATE'] = (daily['FAILURES'] / daily['TOTAL_TESTS'] * 100)
        daily['DAY_NUM'] = range(len(daily))
        
        X = daily[['DAY_NUM']].values
        y = daily['FAILURE_RATE'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next day(s)
        future_days = np.array([[len(daily) + i] for i in range(1, days_ahead + 1)])
        predictions = model.predict(future_days)
        
        # Calculate trend
        slope = model.coef_[0]
        if slope > 0.1:
            trend = "increasing"
        elif slope < -0.1:
            trend = "decreasing"
        else:
            trend = "stable"
        
        confidence = model.score(X, y) * 100
        
        return {
            'next_day_prediction': round(float(predictions[0]), 2),
            'next_week_prediction': round(float(predictions[-1]), 2) if days_ahead >= 7 else round(float(predictions[0]), 2),
            'trend': trend,
            'confidence': round(confidence, 2),
            'slope': round(slope, 3),
            'data_points': len(daily),
            'message': 'Prediction based on linear regression model'
        }
    
    def analyze_api_failures(self):
        """
        Analyze failures by API endpoint
        
        LOGIC:
        1. Groups all test results by API endpoint
        2. Calculates total failures, passes, and average response time
        3. Determines trend by comparing recent vs older data
        4. Assigns severity based on failure rate and trend
        
        TREND CALCULATION:
        - Takes last 3 days of data (recent)
        - Takes first 3 days of data (older)
        - Compares average failure rates
        
        EXAMPLE:
        API: /api/payment/process
        Older 3 days avg: 5% failure rate
        Recent 3 days avg: 12% failure rate
        Difference: 12 - 5 = 7% (> 2%)
        → Trend = "increasing", Severity = "high"
        
        SEVERITY ASSIGNMENT:
        - High: failure_rate > 10% AND increasing
        - Medium: failure_rate 5-10% OR stable
        - Low: failure_rate < 5% OR decreasing
        """
        api_analysis = self.df.groupby('API').agg({
            'FAILURES': 'sum',
            'PASS_COUNT': 'sum',
            'P95_RESPONSE_TIME': 'mean',
            'TOTAL_TESTS': 'sum'
        }).reset_index()
        
        api_analysis['FAILURE_RATE'] = (api_analysis['FAILURES'] / api_analysis['TOTAL_TESTS'] * 100).round(2)
        api_analysis = api_analysis.sort_values('FAILURES', ascending=False)
        
        api_trends = []
        for api in api_analysis['API'].unique():
            api_data = self.df[self.df['API'] == api].sort_values('TEST_DATE')
            if len(api_data) >= 5:
                recent_failure_rate = api_data.tail(3)['FAILURE_RATE'].mean()
                older_failure_rate = api_data.head(3)['FAILURE_RATE'].mean()
                
                if recent_failure_rate > older_failure_rate + 2:
                    trend = 'increasing'
                    severity = 'high' if recent_failure_rate > 10 else 'medium'
                elif recent_failure_rate < older_failure_rate - 2:
                    trend = 'decreasing'
                    severity = 'low'
                else:
                    trend = 'stable'
                    severity = 'medium' if recent_failure_rate > 5 else 'low'
                
                api_trends.append({
                    'api': api,
                    'failures': int(api_data['FAILURES'].sum()),
                    'passes': int(api_data['PASS_COUNT'].sum()),
                    'failure_rate': round(api_data['FAILURE_RATE'].mean(), 2),
                    'p95_response_time': round(api_data['P95_RESPONSE_TIME'].mean(), 2),
                    'trend': trend,
                    'severity': severity,
                    'recent_failure_rate': round(recent_failure_rate, 2),
                    'older_failure_rate': round(older_failure_rate, 2)
                })
        
        return sorted(api_trends, key=lambda x: x['failures'], reverse=True)
    
    def analyze_art_failures(self):
        """
        Analyze failures by ART (Application/Feature)
        
        LOGIC: Same as API analysis but grouped by ART
        Provides high-level view of which application features are failing
        
        EXAMPLE:
        ART: "Payment Module"
        - Contains multiple APIs (/process, /validate, /confirm)
        - Aggregates all their failures together
        - Shows overall health of the payment feature
        """
        art_analysis = self.df.groupby('ART').agg({
            'FAILURES': 'sum',
            'PASS_COUNT': 'sum',
            'P95_RESPONSE_TIME': 'mean',
            'TOTAL_TESTS': 'sum',
            'API': 'count'  # Count of APIs per ART
        }).reset_index()
        
        art_analysis.rename(columns={'API': 'API_COUNT'}, inplace=True)
        art_analysis['FAILURE_RATE'] = (art_analysis['FAILURES'] / art_analysis['TOTAL_TESTS'] * 100).round(2)
        art_analysis = art_analysis.sort_values('FAILURES', ascending=False)
        
        # Calculate trend for each ART
        art_trends = []
        for art in art_analysis['ART'].unique():
            art_data = self.df[self.df['ART'] == art].sort_values('TEST_DATE')
            if len(art_data) >= 5:
                recent_failure_rate = art_data.tail(3)['FAILURE_RATE'].mean()
                older_failure_rate = art_data.head(3)['FAILURE_RATE'].mean()
                
                if recent_failure_rate > older_failure_rate + 2:
                    trend = 'increasing'
                    severity = 'high' if recent_failure_rate > 10 else 'medium'
                elif recent_failure_rate < older_failure_rate - 2:
                    trend = 'decreasing'
                    severity = 'low'
                else:
                    trend = 'stable'
                    severity = 'medium' if recent_failure_rate > 5 else 'low'
                
                art_trends.append({
                    'ART': art,
                    'FAILURES': int(art_data['FAILURES'].sum()),
                    'PASS_COUNT': int(art_data['PASS_COUNT'].sum()),
                    'FAILURE_RATE': round(art_data['FAILURE_RATE'].mean(), 2),
                    'P95_RESPONSE_TIME': round(art_data['P95_RESPONSE_TIME'].mean(), 2),
                    'API_COUNT': len(art_data['API'].unique()),
                    'TOTAL_TESTS': int(art_data['TOTAL_TESTS'].sum()),
                    'trend': trend,
                    'severity': severity
                })
        
        return sorted(art_trends, key=lambda x: x['FAILURES'], reverse=True)
    
    def detect_performance_degradation(self):
        """
        Detect performance degradation in P95 response times
        
        LOGIC:
        1. Calculates daily average P95 response time
        2. Compares recent 3-day average vs first 3-day average
        3. Calculates percentage change
        
        CALCULATION EXAMPLE:
        Baseline (first 3 days): avg = 200ms
        Recent (last 3 days): avg = 260ms
        Degradation = ((260 - 200) / 200) × 100 = 30%
        
        If degradation > 10% → Flag as performance issue
        
        ROLLING AVERAGE:
        Uses 3-day rolling window to smooth out daily spikes
        """
        daily_perf = self.df.groupby('TEST_DATE').agg({
            'P95_RESPONSE_TIME': 'mean'
        }).reset_index()
        
        daily_perf['ROLLING_AVG'] = daily_perf['P95_RESPONSE_TIME'].rolling(window=3, min_periods=1).mean()
        daily_perf['TEST_DATE'] = daily_perf['TEST_DATE'].dt.strftime('%Y-%m-%d')
        
        if len(daily_perf) >= 6:
            recent_avg = daily_perf.tail(3)['P95_RESPONSE_TIME'].mean()
            older_avg = daily_perf.head(3)['P95_RESPONSE_TIME'].mean()
            degradation_pct = ((recent_avg - older_avg) / older_avg * 100)
            
            return {
                'data': daily_perf.to_dict('records'),
                'degradation_pct': round(degradation_pct, 2),
                'is_degrading': degradation_pct > 10,
                'current_avg': round(recent_avg, 2),
                'baseline_avg': round(older_avg, 2)
            }
        
        return {
            'data': daily_perf.to_dict('records'),
            'degradation_pct': 0,
            'is_degrading': False,
            'message': 'Need more data for performance trend analysis'
        }
    
    def identify_instability_hotspots(self):
        """
        Identify unstable APIs/ARTs with high failure variance
        
        INSTABILITY SCORE CALCULATION:
        Score = (Variance × 0.5) + (Avg_Failures × 0.3) + (|Trend| × 0.2)
        
        COMPONENTS:
        1. Variance (50% weight): How much failure rate fluctuates
           - High variance = unpredictable, unstable
           - Example: [2%, 15%, 3%, 18%] → high variance
        
        2. Average Failures (30% weight): Absolute failure count
           - More failures = more concerning
           - Example: 50 failures avg vs 5 failures avg
        
        3. Failure Trend (20% weight): Direction of change
           - Positive trend = getting worse
           - Example: increasing by 5 failures per day
        
        EXAMPLE CALCULATION:
        API: /api/payment/process
        Variance: 12.5
        Avg Failures: 25
        Trend: 3.2
        
        Score = (12.5 × 0.5) + (25 × 0.3) + (3.2 × 0.2)
              = 6.25 + 7.5 + 0.64
              = 14.39
        
        INTERPRETATION:
        Score > 8  → Critical instability
        Score 5-8  → Moderate instability
        Score < 5  → Stable
        """
        api_instability = []
        
        for api in self.df['API'].unique():
            api_data = self.df[self.df['API'] == api].sort_values('TEST_DATE')
            
            if len(api_data) >= 5:
                failure_variance = api_data['FAILURE_RATE'].std()
                avg_failures = api_data['FAILURES'].mean()
                failure_trend = api_data['FAILURES'].diff().mean()
                
                instability_score = (failure_variance * 0.5 + avg_failures * 0.3 + abs(failure_trend) * 0.2)
                
                if instability_score > 2:
                    api_instability.append({
                        'identifier': api,
                        'type': 'API',
                        'instability_score': round(instability_score, 2),
                        'avg_failures': round(avg_failures, 2),
                        'variance': round(failure_variance, 2),
                        'trend_value': round(failure_trend, 2),
                        'total_executions': len(api_data)
                    })
        
        return sorted(api_instability, key=lambda x: x['instability_score'], reverse=True)[:10]
    
    def generate_alerts(self):
        """Generate proactive alerts based on analysis"""
        alerts = []
        
        prediction = self.predict_failure_rate()
        if prediction.get('next_day_prediction', 0) > 8:
            alerts.append({
                'type': 'critical',
                'severity': 'high',
                'message': f"Predicted failure rate of {prediction['next_day_prediction']}% exceeds threshold",
                'category': 'Prediction',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        api_failures = self.analyze_api_failures()
        for api in api_failures[:3]:
            if api['severity'] in ['high'] and api['trend'] == 'increasing':
                alerts.append({
                    'type': 'warning',
                    'severity': api['severity'],
                    'message': f"API '{api['api']}' showing {api['trend']} failures ({api['failure_rate']}%)",
                    'category': 'API Health',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        perf = self.detect_performance_degradation()
        if perf.get('is_degrading'):
            alerts.append({
                'type': 'warning',
                'severity': 'medium',
                'message': f"Performance degraded by {perf['degradation_pct']}% - P95 response time increasing",
                'category': 'Performance',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        hotspots = self.identify_instability_hotspots()
        for hotspot in hotspots[:2]:
            if hotspot['instability_score'] > 8:
                alerts.append({
                    'type': 'warning',
                    'severity': 'high',
                    'message': f"High instability in {hotspot['identifier']} (score: {hotspot['instability_score']})",
                    'category': 'Stability',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return alerts
    
    def get_recommendations(self):
        """Generate AI-powered recommendations"""
        recommendations = []
        
        api_failures = self.analyze_api_failures()
        perf = self.detect_performance_degradation()
        hotspots = self.identify_instability_hotspots()
        
        critical_apis = [api for api in api_failures if api['severity'] in ['high']]
        if critical_apis:
            recommendations.append({
                'priority': 'high',
                'title': 'Critical API Failures Detected',
                'description': f"{len(critical_apis)} APIs showing critical failure rates",
                'actions': [
                    f"Review {critical_apis[0]['api']} (failure rate: {critical_apis[0]['failure_rate']}%)",
                    "Implement additional error handling and retry logic",
                    "Consider circuit breaker pattern for failing endpoints"
                ]
            })
        
        if perf.get('is_degrading'):
            recommendations.append({
                'priority': 'medium',
                'title': 'Performance Degradation Detected',
                'description': f"P95 response time increased by {perf['degradation_pct']}%",
                'actions': [
                    "Profile slow APIs and optimize database queries",
                    "Check for resource contention or memory leaks",
                    "Consider implementing caching strategies"
                ]
            })
        
        if hotspots:
            recommendations.append({
                'priority': 'high',
                'title': 'Code Instability Detected',
                'description': f"{len(hotspots)} endpoints showing high instability",
                'actions': [
                    f"Refactor {hotspots[0]['identifier']} - unstable with score {hotspots[0]['instability_score']}",
                    "Increase test coverage for volatile components",
                    "Implement better error logging and monitoring"
                ]
            })
        
        return recommendations
    
    def get_art_specific_data(self, art_name):
        """Get detailed data for specific ART"""
        art_data = self.df[self.df['ART'] == art_name]
        
        if len(art_data) == 0:
            return {'error': 'ART not found'}
        
        # APIs under this ART
        apis = self.analyze_api_failures_for_art(art_name)
        
        # Daily metrics for this ART
        daily = art_data.groupby('TEST_DATE').agg({
            'PASS_COUNT': 'sum',
            'FAILURES': 'sum',
            'P95_RESPONSE_TIME': 'mean',
            'TOTAL_TESTS': 'sum'
        }).reset_index()
        daily['FAILURE_RATE'] = (daily['FAILURES'] / daily['TOTAL_TESTS'] * 100).round(2)
        daily['TEST_DATE'] = daily['TEST_DATE'].dt.strftime('%Y-%m-%d')
        
        return {
            'art_name': art_name,
            'apis': apis,
            'daily_metrics': daily.to_dict('records'),
            'summary': {
                'total_tests': int(art_data['TOTAL_TESTS'].sum()),
                'total_failures': int(art_data['FAILURES'].sum()),
                'total_passes': int(art_data['PASS_COUNT'].sum()),
                'avg_failure_rate': round(art_data['FAILURE_RATE'].mean(), 2),
                'avg_p95': round(art_data['P95_RESPONSE_TIME'].mean(), 2)
            }
        }
    
    def analyze_api_failures_for_art(self, art_name):
        """Get API analysis for specific ART"""
        art_data = self.df[self.df['ART'] == art_name]
        
        api_analysis = art_data.groupby('API').agg({
            'FAILURES': 'sum',
            'PASS_COUNT': 'sum',
            'P95_RESPONSE_TIME': 'mean',
            'TOTAL_TESTS': 'sum'
        }).reset_index()
        
        api_analysis['FAILURE_RATE'] = (api_analysis['FAILURES'] / api_analysis['TOTAL_TESTS'] * 100).round(2)
        return api_analysis.sort_values('FAILURES', ascending=False).to_dict('records')
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("✓ Database connection closed")

# Initialize analyzer
analyzer = CICDAnalyzer()

@app.route('/')
def index():
    """Serve the dashboard HTML"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Backend is running',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get all dashboard data"""
    days = int(request.args.get('days', 7))
    
    try:
        if analyzer.df is None or len(analyzer.df) == 0:
            if not analyzer.connect_db():
                return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
            analyzer.fetch_test_results(days)
        elif 'requested_days' not in dir(analyzer) or analyzer.requested_days != days:
            analyzer.fetch_test_results(days)
        
        analyzer.requested_days = days
        
        return jsonify({
            'status': 'success',
            'daily_metrics': analyzer.calculate_daily_metrics(),
            'predictions': analyzer.predict_failure_rate(days_ahead=7),
            'api_failures': analyzer.analyze_api_failures(),
            'art_failures': analyzer.analyze_art_failures(),
            'performance': analyzer.detect_performance_degradation(),
            'instability_hotspots': analyzer.identify_instability_hotspots(),
            'alerts': analyzer.generate_alerts(),
            'recommendations': analyzer.get_recommendations()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/art/<art_name>', methods=['GET'])
def get_art_data(art_name):
    """Get data for specific ART"""
    try:
        days = int(request.args.get('days', 7))
        if analyzer.df is None:
            analyzer.connect_db()
            analyzer.fetch_test_results(days)
        
        data = analyzer.get_art_specific_data(art_name)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/arts', methods=['GET'])
def get_all_arts():
    """Get list of all ARTs"""
    try:
        if analyzer.df is None:
            analyzer.connect_db()
            analyzer.fetch_test_results(30)
        
        arts = sorted(analyzer.df['ART'].unique().tolist())
        return jsonify({'status': 'success', 'arts': arts})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("CI/CD NFT Test Analysis System")
    print("=" * 60)
    print("Server starting on http://localhost:5000")
    print("Dashboard available at: http://localhost:5000")
    print("Health check: http://localhost:5000/api/health")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
    