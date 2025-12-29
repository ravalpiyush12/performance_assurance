"""
HTML Dashboard Generator for Production vs PTE Analysis
Generates interactive HTML reports with charts and visualizations
"""

from typing import Dict, List
from datetime import datetime
import json


class HTMLDashboardGenerator:
    """Generate interactive HTML dashboard from analysis report"""
    
    def __init__(self, report: Dict):
        self.report = report
        
    def generate(self, output_file: str = None) -> str:
        """Generate complete HTML dashboard"""
        if output_file is None:
            output_file = f"dashboard_{self.report['analysis_id']}.html"
        
        html_content = self._build_html()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file
    
    def _build_html(self) -> str:
        """Build complete HTML content"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Production vs PTE Analysis Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_header()}
        {self._generate_key_metrics()}
        {self._generate_two_column_section()}
        {self._generate_response_time_chart()}
        {self._generate_resource_charts()}
        {self._generate_discrepancies_table()}
        {self._generate_recommendations()}
        {self._generate_coverage_chart()}
        {self._generate_untested_endpoints()}
    </div>
    
    <script>
        {self._generate_chart_scripts()}
    </script>
</body>
</html>"""
    
    def _get_css(self) -> str:
        """Return CSS styles"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }

        .header h1 {
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header .subtitle {
            color: #718096;
            font-size: 1.1em;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-5px);
        }

        .metric-card .label {
            color: #718096;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
            font-weight: 600;
        }

        .metric-card .value {
            color: #2d3748;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .metric-card .comparison {
            font-size: 0.9em;
            margin-top: 10px;
            padding: 8px;
            border-radius: 5px;
        }

        .comparison.good {
            background: #d4edda;
            color: #155724;
        }

        .comparison.warning {
            background: #fff3cd;
            color: #856404;
        }

        .comparison.critical {
            background: #f8d7da;
            color: #721c24;
        }

        .chart-container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .chart-container h2 {
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 1.5em;
        }

        .chart-wrapper {
            position: relative;
            height: 400px;
        }

        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        .score-card {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }

        .score-value {
            font-size: 5em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 20px 0;
        }

        .score-rating {
            font-size: 1.5em;
            color: #4a5568;
            margin-bottom: 20px;
        }

        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e2e8f0;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            background: #f7fafc;
            color: #2d3748;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e2e8f0;
        }

        td {
            padding: 15px;
            border-bottom: 1px solid #e2e8f0;
        }

        .severity-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }

        .severity-critical {
            background: #feb2b2;
            color: #742a2a;
        }

        .severity-high {
            background: #fbd38d;
            color: #7c2d12;
        }

        .severity-medium {
            background: #faf089;
            color: #744210;
        }

        .severity-low {
            background: #c6f6d5;
            color: #22543d;
        }

        .recommendations {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .recommendation-item {
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            background: #f7fafc;
            border-radius: 5px;
        }

        .recommendation-item h3 {
            color: #2d3748;
            margin-bottom: 10px;
        }

        .recommendation-item p {
            color: #4a5568;
            line-height: 1.6;
        }

        .endpoint-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .endpoint-item {
            background: #f7fafc;
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #ef4444;
        }

        .endpoint-item .method {
            font-weight: bold;
            color: #667eea;
            margin-right: 10px;
        }

        @media (max-width: 768px) {
            .two-column {
                grid-template-columns: 1fr;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _generate_header(self) -> str:
        """Generate header section"""
        return f"""
        <div class="header">
            <h1>🚀 Production vs PTE Traffic Analysis</h1>
            <p class="subtitle">Analysis ID: {self.report['analysis_id']} | Generated: {self.report['timestamp']}</p>
        </div>
        """
    
    def _generate_key_metrics(self) -> str:
        """Generate key metrics cards"""
        summary = self.report['summary']
        efficacy = self.report['test_efficacy']
        
        efficacy_class = self._get_status_class(efficacy['overall_efficacy_score'])
        coverage_class = self._get_status_class(summary['test_coverage_pct'])
        
        return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="label">Test Efficacy Score</div>
                <div class="value">{efficacy['overall_efficacy_score']:.1f}%</div>
                <div class="comparison {efficacy_class}">{self._get_emoji(efficacy_class)} {efficacy['rating']}</div>
            </div>
            <div class="metric-card">
                <div class="label">Endpoint Coverage</div>
                <div class="value">{summary['test_coverage_pct']:.1f}%</div>
                <div class="comparison {coverage_class}">{self._get_emoji(coverage_class)} {self.report['coverage_gaps']['untested_endpoints']} endpoints untested</div>
            </div>
            <div class="metric-card">
                <div class="label">Critical Issues</div>
                <div class="value">{summary['critical_issues']}</div>
                <div class="comparison critical">🔴 Requires immediate attention</div>
            </div>
            <div class="metric-card">
                <div class="label">High Priority Issues</div>
                <div class="value">{summary['high_priority_issues']}</div>
                <div class="comparison warning">⚠️ Address before next release</div>
            </div>
        </div>
        """
    
    def _generate_two_column_section(self) -> str:
        """Generate two-column layout with score card and request rate chart"""
        efficacy = self.report['test_efficacy']
        
        return f"""
        <div class="two-column">
            <div class="score-card">
                <h2>Overall Test Efficacy</h2>
                <div class="score-value">{efficacy['overall_efficacy_score']:.1f}</div>
                <div class="score-rating">{efficacy['rating']} Rating</div>
                
                <div style="text-align: left; margin-top: 20px;">
                    <p style="margin-bottom: 10px; color: #4a5568;"><strong>Coverage Score:</strong></p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {efficacy['coverage_score']}%">{efficacy['coverage_score']:.1f}%</div>
                    </div>
                    
                    <p style="margin: 15px 0 10px; color: #4a5568;"><strong>Load Coverage:</strong></p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {efficacy['load_coverage_score']}%">{efficacy['load_coverage_score']:.1f}%</div>
                    </div>
                    
                    <p style="margin: 15px 0 10px; color: #4a5568;"><strong>Performance Score:</strong></p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {efficacy['performance_score']}%; background: {'#667eea' if efficacy['performance_score'] > 70 else '#f59e0b' if efficacy['performance_score'] > 40 else '#ef4444'};">{efficacy['performance_score']:.1f}%</div>
                    </div>
                    
                    <p style="margin: 15px 0 10px; color: #4a5568;"><strong>Error Validation:</strong></p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {max(5, efficacy['error_validation_score'])}%; background: {'#667eea' if efficacy['error_validation_score'] > 70 else '#f59e0b' if efficacy['error_validation_score'] > 40 else '#ef4444'};">{efficacy['error_validation_score']:.1f}%</div>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <h2>Production vs PTE: Request Rate</h2>
                <div class="chart-wrapper">
                    <canvas id="requestRateChart"></canvas>
                </div>
            </div>
        </div>
        """
    
    def _generate_response_time_chart(self) -> str:
        """Generate response time comparison chart"""
        return """
        <div class="chart-container">
            <h2>Response Time Percentiles Comparison</h2>
            <div class="chart-wrapper">
                <canvas id="responseTimeChart"></canvas>
            </div>
        </div>
        """
    
    def _generate_resource_charts(self) -> str:
        """Generate resource utilization and traffic pattern charts"""
        return """
        <div class="two-column">
            <div class="chart-container">
                <h2>Resource Utilization</h2>
                <div class="chart-wrapper">
                    <canvas id="resourceChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>Production Traffic Pattern (24h)</h2>
                <div class="chart-wrapper">
                    <canvas id="trafficPatternChart"></canvas>
                </div>
            </div>
        </div>
        """
    
    def _generate_discrepancies_table(self) -> str:
        """Generate discrepancies table"""
        rows = ""
        for disc in self.report['discrepancies']:
            if disc['severity'] in ['critical', 'high']:
                discrepancy_sign = "+" if disc['discrepancy_pct'] > 0 else ""
                rows += f"""
                <tr>
                    <td><strong>{disc['metric']}</strong></td>
                    <td>{disc['prod_value']:.2f}</td>
                    <td>{disc['pte_value']:.2f}</td>
                    <td>{discrepancy_sign}{disc['discrepancy_pct']:.1f}%</td>
                    <td><span class="severity-badge severity-{disc['severity']}">{disc['severity'].title()}</span></td>
                </tr>
                """
        
        return f"""
        <div class="chart-container">
            <h2>🔍 Critical Discrepancies</h2>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Production</th>
                        <th>PTE</th>
                        <th>Discrepancy</th>
                        <th>Severity</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_recommendations(self) -> str:
        """Generate recommendations section"""
        recommendations = self._build_recommendations()
        
        items = ""
        for i, rec in enumerate(recommendations, 1):
            items += f"""
            <div class="recommendation-item">
                <h3>{i}. {rec['title']}</h3>
                <p>{rec['description']}</p>
            </div>
            """
        
        return f"""
        <div class="recommendations">
            <h2>📋 Key Recommendations</h2>
            {items}
        </div>
        """
    
    def _generate_coverage_chart(self) -> str:
        """Generate coverage donut chart"""
        return """
        <div class="chart-container">
            <h2>Endpoint Test Coverage</h2>
            <div class="chart-wrapper" style="height: 300px;">
                <canvas id="coverageChart"></canvas>
            </div>
        </div>
        """
    
    def _generate_untested_endpoints(self) -> str:
        """Generate untested endpoints section"""
        untested = self.report['coverage_gaps'].get('untested_list', [])
        
        if not untested:
            return ""
        
        items = ""
        for endpoint in untested[:20]:  # Show top 20
            items += f"""
            <div class="endpoint-item">
                <span class="method">{endpoint['http_method']}</span>
                <span>{endpoint['endpoint_name']}</span>
            </div>
            """
        
        return f"""
        <div class="chart-container">
            <h2>⚠️ Untested Endpoints</h2>
            <p style="color: #4a5568; margin-bottom: 15px;">
                The following {len(untested)} endpoints are active in production but were not included in PTE certification testing:
            </p>
            <div class="endpoint-list">
                {items}
            </div>
        </div>
        """
    
    def _generate_chart_scripts(self) -> str:
        """Generate Chart.js scripts"""
        prod = self.report['production_baseline']
        pte = self.report['pte_metrics']
        patterns = self.report['production_patterns']
        coverage = self.report['coverage_gaps']
        
        # Extract hourly pattern data
        hourly_labels = []
        hourly_data = []
        if 'hourly_pattern' in patterns and patterns['hourly_pattern']:
            sorted_hours = sorted(patterns['hourly_pattern'].items(), key=lambda x: int(x[0]))
            hourly_labels = [f"{h}h" for h, _ in sorted_hours[::2]]  # Every 2 hours
            hourly_data = [v for _, v in sorted_hours[::2]]
        
        return f"""
        Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        Chart.defaults.color = '#4a5568';

        // Request Rate Comparison
        new Chart(document.getElementById('requestRateChart'), {{
            type: 'bar',
            data: {{
                labels: ['Average', 'Peak'],
                datasets: [{{
                    label: 'Production',
                    data: [{prod.get('avg_request_rate', 0):.2f}, {prod.get('peak_request_rate', 0):.2f}],
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }}, {{
                    label: 'PTE',
                    data: [{pte.get('avg_request_rate_tested', 0):.2f}, {pte.get('max_request_rate_tested', 0):.2f}],
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: 'rgba(239, 68, 68, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: true, position: 'top' }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Requests per Second' }}
                    }}
                }}
            }}
        }});

        // Response Time Comparison
        new Chart(document.getElementById('responseTimeChart'), {{
            type: 'line',
            data: {{
                labels: ['P50', 'P95', 'P99'],
                datasets: [{{
                    label: 'Production',
                    data: [{prod.get('avg_response_time', 0):.2f}, {prod.get('p95_response_time', 0):.2f}, {prod.get('p99_response_time', 0):.2f}],
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true
                }}, {{
                    label: 'PTE',
                    data: [{pte.get('avg_response_time', 0):.2f}, {pte.get('p95_response_time', 0):.2f}, {pte.get('p99_response_time', 0):.2f}],
                    borderColor: 'rgba(239, 68, 68, 1)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Response Time (ms)' }}
                    }}
                }}
            }}
        }});

        // Resource Utilization
        new Chart(document.getElementById('resourceChart'), {{
            type: 'radar',
            data: {{
                labels: ['CPU', 'Memory', 'Throughput', 'Concurrency'],
                datasets: [{{
                    label: 'Production',
                    data: [{prod.get('peak_cpu', 0):.1f}, {prod.get('peak_memory', 0):.1f}, {min(100, prod.get('peak_throughput', 0)/20):.1f}, {min(100, prod.get('peak_concurrent_users', 0)/100):.1f}],
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderWidth: 2
                }}, {{
                    label: 'PTE',
                    data: [{pte.get('peak_cpu', 0):.1f}, {pte.get('peak_memory', 0):.1f}, {min(100, pte.get('max_throughput', 0)/20):.1f}, {min(100, pte.get('max_concurrent_users', 0)/100):.1f}],
                    borderColor: 'rgba(239, 68, 68, 1)',
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{ beginAtZero: true, max: 100 }}
                }}
            }}
        }});

        // Traffic Pattern
        new Chart(document.getElementById('trafficPatternChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(hourly_labels)},
                datasets: [{{
                    label: 'Request Rate',
                    data: {json.dumps(hourly_data)},
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Requests per Second' }}
                    }}
                }}
            }}
        }});

        // Coverage Chart
        new Chart(document.getElementById('coverageChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Tested Endpoints', 'Untested Endpoints'],
                datasets: [{{
                    data: [{coverage.get('tested_endpoints', 0)}, {coverage.get('untested_endpoints', 0)}],
                    backgroundColor: ['rgba(102, 126, 234, 0.8)', 'rgba(239, 68, 68, 0.8)'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom' }} }}
            }}
        }});
        """
    
    def _build_recommendations(self) -> List[Dict]:
        """Build recommendations from analysis"""
        recommendations = []
        prod = self.report['production_baseline']
        pte = self.report['pte_metrics']
        coverage = self.report['coverage_gaps']
        
        # Load testing recommendation
        if pte.get('max_request_rate_tested', 0) < prod.get('peak_request_rate', 0):
            target = prod.get('peak_request_rate', 0) * 1.5
            recommendations.append({
                'title': 'Increase Load Testing Capacity',
                'description': f"PTE testing only reached {pte.get('max_request_rate_tested', 0):.0f} req/s compared to production peak of {prod.get('peak_request_rate', 0):.0f} req/s. Increase test load to minimum {target:.0f} req/s (150% of production peak) to ensure adequate headroom for traffic spikes."
            })
        
        # Error rate recommendation
        for disc in self.report['discrepancies']:
            if disc['metric'] == 'Error Rate' and disc['severity'] == 'critical':
                recommendations.append({
                    'title': 'Investigate Error Rate Discrepancy',
                    'description': f"Production error rate ({disc['prod_value']:.3f}%) differs significantly from PTE predictions ({disc['pte_value']:.3f}%). This suggests either production environment issues or inadequate error scenario coverage in PTE. Conduct immediate investigation."
                })
                break
        
        # Coverage recommendation
        if coverage.get('coverage_percentage', 0) < 90:
            untested = coverage.get('untested_endpoints', 0)
            recommendations.append({
                'title': 'Test Missing Endpoints',
                'description': f"{untested} production endpoints remain untested. Add these to the next PTE certification cycle to achieve >90% coverage and ensure comprehensive system validation."
            })
        
        # Duration recommendation
        recommendations.append({
            'title': 'Extend Test Duration',
            'description': 'Run sustained load tests for minimum 60 minutes to identify memory leaks, connection pool exhaustion, and other time-dependent issues not visible in shorter tests.'
        })
        
        # Spike testing recommendation
        recommendations.append({
            'title': 'Implement Spike Testing',
            'description': f"Add spike test scenarios at 2x production peak ({prod.get('peak_request_rate', 0) * 2:.0f} req/s) to validate system resilience under extreme load conditions and verify graceful degradation."
        })
        
        return recommendations
    
    def _get_status_class(self, score: float) -> str:
        """Get CSS class based on score"""
        if score >= 80:
            return 'good'
        elif score >= 60:
            return 'warning'
        else:
            return 'critical'
    
    def _get_emoji(self, status_class: str) -> str:
        """Get emoji for status"""
        return {
            'good': '✅',
            'warning': '⚠️',
            'critical': '🔴'
        }.get(status_class, '⚠️')


# Integration with main analysis function
def generate_html_dashboard(report: Dict, output_file: str = None) -> str:
    """
    Generate HTML dashboard from analysis report
    
    Args:
        report: Analysis report dictionary from run_comprehensive_analysis()
        output_file: Optional output filename
    
    Returns:
        Path to generated HTML file
    """
    generator = HTMLDashboardGenerator(report)
    return generator.generate(output_file)


# Example usage
if __name__ == "__main__":
    # Assuming you have run the analysis
    # report = run_comprehensive_analysis(db_config)
    
    # Generate HTML dashboard
    # html_file = generate_html_dashboard(report)
    # print(f"HTML dashboard generated: {html_file}")
    pass
