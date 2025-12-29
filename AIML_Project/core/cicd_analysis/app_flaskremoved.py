import cx_Oracle 
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
import warnings
import os
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
        """Fetch test results from PTE table"""
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
        """Calculate daily aggregated metrics"""
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
        """Predict failure rate using linear regression"""
        daily = self.df.groupby('TEST_DATE').agg({
            'FAILURES': 'sum',
            'TOTAL_TESTS': 'sum'
        }).reset_index()
        
        daily['FAILURE_RATE'] = (daily['FAILURES'] / daily['TOTAL_TESTS'] * 100)
        daily['DAY_NUM'] = range(len(daily))
        
        X = daily[['DAY_NUM']].values
        y = daily['FAILURE_RATE'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next day(s)
        future_days = np.array([[len(daily) + i] for i in range(days_ahead)])
        predictions = model.predict(future_days)
        
        # Calculate trend
        trend = "increasing" if model.coef_[0] > 0.1 else "decreasing" if model.coef_[0] < -0.1 else "stable"
        
        return {
            'next_day_prediction': round(float(predictions[0]), 2),
            'next_week_prediction': round(float(predictions[-1]), 2) if days_ahead == 7 else None,
            'trend': trend,
            'confidence': round(model.score(X, y) * 100, 2)
        }
    
    def analyze_api_failures(self):
        """Analyze failures by API endpoint"""
        api_analysis = self.df.groupby('API').agg({
            'FAILURES': 'sum',
            'PASS_COUNT': 'sum',
            'P95_RESPONSE_TIME': 'mean',
            'TOTAL_TESTS': 'sum'
        }).reset_index()
        
        api_analysis['FAILURE_RATE'] = (api_analysis['FAILURES'] / api_analysis['TOTAL_TESTS'] * 100).round(2)
        api_analysis = api_analysis.sort_values('FAILURES', ascending=False)
        
        # Calculate trend for each API
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
                    'failure_rate': round(api_data['FAILURE_RATE'].mean(), 2),
                    'p95_response_time': round(api_data['P95_RESPONSE_TIME'].mean(), 2),
                    'trend': trend,
                    'severity': severity
                })
        
        return sorted(api_trends, key=lambda x: x['failures'], reverse=True)
    
    def analyze_art_failures(self):
        """Analyze failures by ART (Application/Feature)"""
        art_analysis = self.df.groupby('ART').agg({
            'FAILURES': 'sum',
            'PASS_COUNT': 'sum',
            'P95_RESPONSE_TIME': 'mean',
            'TOTAL_TESTS': 'sum'
        }).reset_index()
        
        art_analysis['FAILURE_RATE'] = (art_analysis['FAILURES'] / art_analysis['TOTAL_TESTS'] * 100).round(2)
        art_analysis = art_analysis.sort_values('FAILURES', ascending=False)
        
        return art_analysis.head(10).to_dict('records')
    
    def detect_performance_degradation(self):
        """Detect performance degradation in P95 response times"""
        daily_perf = self.df.groupby('TEST_DATE').agg({
            'P95_RESPONSE_TIME': 'mean'
        }).reset_index()
        
        daily_perf['ROLLING_AVG'] = daily_perf['P95_RESPONSE_TIME'].rolling(window=3).mean()
        daily_perf['TEST_DATE'] = daily_perf['TEST_DATE'].dt.strftime('%Y-%m-%d')
        
        # Calculate trend
        if len(daily_perf) >= 7:
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
        
        return {'data': daily_perf.to_dict('records')}
    
    def identify_instability_hotspots(self):
        """Identify unstable APIs/ARTs with high failure variance"""
        api_instability = []
        
        for api in self.df['API'].unique():
            api_data = self.df[self.df['API'] == api]
            
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
                        'total_executions': len(api_data)
                    })
        
        return sorted(api_instability, key=lambda x: x['instability_score'], reverse=True)[:10]
    
    def generate_alerts(self):
        """Generate proactive alerts based on analysis"""
        alerts = []
        
        # Prediction-based alerts
        prediction = self.predict_failure_rate()
        if prediction['next_day_prediction'] > 8:
            alerts.append({
                'type': 'critical',
                'severity': 'high',
                'message': f"Predicted failure rate of {prediction['next_day_prediction']}% exceeds threshold",
                'category': 'Prediction',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # API failure alerts
        api_failures = self.analyze_api_failures()
        for api in api_failures[:3]:
            if api['severity'] in ['high', 'critical'] and api['trend'] == 'increasing':
                alerts.append({
                    'type': 'warning',
                    'severity': api['severity'],
                    'message': f"API '{api['api']}' showing {api['trend']} failures ({api['failure_rate']}%)",
                    'category': 'API Health',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Performance degradation alerts
        perf = self.detect_performance_degradation()
        if perf.get('is_degrading'):
            alerts.append({
                'type': 'warning',
                'severity': 'medium',
                'message': f"Performance degraded by {perf['degradation_pct']}% - P95 response time increasing",
                'category': 'Performance',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Instability alerts
        hotspots = self.identify_instability_hotspots()
        for hotspot in hotspots[:2]:
            if hotspot['instability_score'] > 8:
                alerts.append({
                    'type': 'warning',
                    'severity': 'high',
                    'message': f"High instability detected in {hotspot['identifier']} (score: {hotspot['instability_score']})",
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
        
        # High failure rate recommendations
        critical_apis = [api for api in api_failures if api['severity'] in ['high', 'critical']]
        if critical_apis:
            recommendations.append({
                'priority': 'high',
                'title': 'Critical API Failures Detected',
                'description': f"{len(critical_apis)} APIs showing critical failure rates",
                'actions': [
                    f"Review and fix {critical_apis[0]['api']} (failure rate: {critical_apis[0]['failure_rate']}%)",
                    "Implement additional error handling and retry logic",
                    "Consider circuit breaker pattern for failing endpoints"
                ]
            })
        
        # Performance recommendations
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
        
        # Instability recommendations
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

@app.route('/api/init', methods=['POST'])
def initialize():
    """Initialize connection and fetch data"""
    days = request.json.get('days', 30) if request.json else 30
    
    if analyzer.connect_db():
        data = analyzer.fetch_test_results(days)
        if data is not None:
            return jsonify({
                'status': 'success',
                'message': f'Loaded {len(data)} records',
                'records': len(data)
            })
    
    return jsonify({'status': 'error', 'message': 'Failed to initialize'}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get all dashboard data"""
    days = int(request.args.get('days', 30))
    
    try:
        if analyzer.df is None or len(analyzer.df) == 0:
            if not analyzer.connect_db():
                return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
            analyzer.fetch_test_results(days)
        
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

@app.route('/api/metrics/daily', methods=['GET'])
def get_daily_metrics():
    """Get daily aggregated metrics"""
    return jsonify(analyzer.calculate_daily_metrics())

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    """Get failure rate predictions"""
    return jsonify(analyzer.predict_failure_rate(days_ahead=7))

@app.route('/api/analysis/api', methods=['GET'])
def get_api_analysis():
    """Get API-level failure analysis"""
    return jsonify(analyzer.analyze_api_failures())

@app.route('/api/analysis/art', methods=['GET'])
def get_art_analysis():
    """Get ART-level failure analysis"""
    return jsonify(analyzer.analyze_art_failures())

@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get performance analysis"""
    return jsonify(analyzer.detect_performance_degradation())

@app.route('/api/instability', methods=['GET'])
def get_instability():
    """Get instability hotspots"""
    return jsonify(analyzer.identify_instability_hotspots())

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get current alerts"""
    return jsonify(analyzer.generate_alerts())

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """Get AI recommendations"""
    return jsonify(analyzer.get_recommendations())

if __name__ == '__main__':
    print("=" * 60)
    print("CI/CD NFT Test Analysis System")
    print("=" * 60)
    print("Server starting on http://localhost:5000")
    print("Dashboard available at: http://localhost:5000")
    print("Health check: http://localhost:5000/api/health")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
