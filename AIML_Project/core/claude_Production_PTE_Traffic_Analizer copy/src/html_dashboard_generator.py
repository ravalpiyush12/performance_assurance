"""
HTML Dashboard Generator for Custom PROD/PTE Analysis
Generates interactive dashboards for api_endpoint comparison data
"""

from typing import Dict, List
import json


class CustomHTMLDashboard:
    """Generate HTML dashboard for custom prod/pte analysis"""
    
    def __init__(self, report: Dict):
        self.report = report
    
    def generate(self, output_file: str = None) -> str:
        """Generate HTML dashboard"""
        if output_file is None:
            output_file = f"dashboard_{self.report['analysis_id']}.html"
        
        html = self._build_html()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Dashboard generated: {output_file}")
        return output_file
    
    def _build_html(self) -> str:
        """Build complete HTML"""
        prod = self.report['production_metrics']
        pte = self.report['pte_metrics']
        summary = self.report['summary']
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Endpoint Analysis: Production vs PTE</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    {self._get_styles()}
</head>
<body>
    <div class="container">
        {self._header()}
        {self._summary_cards()}
        {self._metrics_comparison()}
        {self._duration_charts()}
        {self._endpoint_tables()}
        {self._issues_table()}
        {self._coverage_section()}
    </div>
    {self._chart_scripts()}
</body>
</html>"""
    
    def _get_styles(self) -> str:
        """CSS styles"""
        return """<style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container { max-width: 1400px; margin: 0 auto; }
        
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
        
        .subtitle { color: #718096; font-size: 1.1em; }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        
        .metric-card:hover { transform: translateY(-5px); }
        
        .metric-card .label {
            color: #718096;
            font-size: 0.85em;
            margin-bottom: 10px;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .metric-card .value {
            color: #2d3748;
            font-size: 2.2em;
            font-weight: bold;
        }
        
        .metric-card .subvalue {
            color: #a0aec0;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-top: 10px;
        }
        
        .status-good { background: #c6f6d5; color: #22543d; }
        .status-warning { background: #feebc8; color: #7c2d12; }
        .status-critical { background: #fed7d7; color: #742a2a; }
        
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
        
        .chart-wrapper { position: relative; height: 400px; }
        
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        
        th {
            background: #f7fafc;
            color: #2d3748;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e2e8f0;
            font-size: 0.9em;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
            font-size: 0.9em;
        }
        
        tr:hover { background: #f7fafc; }
        
        .endpoint-name {
            font-family: 'Courier New', monospace;
            color: #667eea;
            font-weight: 500;
        }
        
        .severity-critical { color: #e53e3e; font-weight: bold; }
        .severity-high { color: #dd6b20; font-weight: bold; }
        .severity-medium { color: #d69e2e; }
        .severity-low { color: #38a169; }
        
        .untested-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .untested-item {
            background: #fff5f5;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #e53e3e;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .two-column, .metrics-grid { grid-template-columns: 1fr; }
        }
        </style>"""
    
    def _header(self) -> str:
        """Header section"""
        return f"""
        <div class="header">
            <h1>📊 API Endpoint Analysis: Production vs PTE</h1>
            <p class="subtitle">Analysis ID: {self.report['analysis_id']} | Generated: {self.report['timestamp']}</p>
        </div>
        """
    
    def _summary_cards(self) -> str:
        """Summary metric cards"""
        summary = self.report['summary']
        prod = self.report['production_metrics']
        pte = self.report['pte_metrics']
        
        coverage_status = 'good' if summary['coverage_pct'] > 80 else 'warning' if summary['coverage_pct'] > 60 else 'critical'
        
        return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="label">Total Comparisons</div>
                <div class="value">{summary['total_comparisons']}</div>
                <div class="subvalue">Endpoints analyzed</div>
            </div>
            <div class="metric-card">
                <div class="label">Critical Issues</div>
                <div class="value">{summary['critical_issues']}</div>
                <span class="status-badge status-{'critical' if summary['critical_issues'] > 0 else 'good'}">
                    {'⚠️ Action Required' if summary['critical_issues'] > 0 else '✓ No Issues'}
                </span>
            </div>
            <div class="metric-card">
                <div class="label">High Issues</div>
                <div class="value">{summary['high_issues']}</div>
                <span class="status-badge status-{'warning' if summary['high_issues'] > 0 else 'good'}">
                    {'⚠️ Review Needed' if summary['high_issues'] > 0 else '✓ No Issues'}
                </span>
            </div>
            <div class="metric-card">
                <div class="label">Test Results</div>
                <div class="value">{summary['passed_tests']}/{summary['total_comparisons']}</div>
                <div class="subvalue">Passed tests</div>
            </div>
            <div class="metric-card">
                <div class="label">Coverage</div>
                <div class="value">{summary['coverage_pct']:.1f}%</div>
                <span class="status-badge status-{coverage_status}">
                    {self.report['coverage']['untested_endpoints']} untested
                </span>
            </div>
        </div>
        """
    
    def _metrics_comparison(self) -> str:
        """Metrics comparison section"""
        prod = self.report['production_metrics']
        pte = self.report['pte_metrics']
        
        return f"""
        <div class="two-column">
            <div class="chart-container">
                <h2>Production Metrics (Last 7 Days)</h2>
                <table>
                    <tr>
                        <td><strong>Total API Calls</strong></td>
                        <td>{prod.get('total_calls', 0):,}</td>
                    </tr>
                    <tr>
                        <td><strong>Unique Endpoints</strong></td>
                        <td>{prod.get('total_endpoints', 0)}</td>
                    </tr>
                    <tr>
                        <td><strong>Avg Duration</strong></td>
                        <td>{prod.get('overall_avg_duration', 0):.2f} ms</td>
                    </tr>
                    <tr>
                        <td><strong>P90 Duration</strong></td>
                        <td>{prod.get('overall_p90_duration', 0):.2f} ms</td>
                    </tr>
                    <tr>
                        <td><strong>P95 Duration</strong></td>
                        <td>{prod.get('overall_p95_duration', 0):.2f} ms</td>
                    </tr>
                    <tr>
                        <td><strong>Slowest Endpoint</strong></td>
                        <td class="endpoint-name">{prod.get('slowest_endpoint', 'N/A')[:50]}</td>
                    </tr>
                </table>
            </div>
            
            <div class="chart-container">
                <h2>PTE Metrics (Last 30 Days)</h2>
                <table>
                    <tr>
                        <td><strong>Total API Calls</strong></td>
                        <td>{pte.get('total_calls', 0):,}</td>
                    </tr>
                    <tr>
                        <td><strong>Endpoints Tested</strong></td>
                        <td>{pte.get('total_endpoints_tested', 0)}</td>
                    </tr>
                    <tr>
                        <td><strong>Avg Duration</strong></td>
                        <td>{pte.get('overall_avg_duration', 0):.2f} ms</td>
                    </tr>
                    <tr>
                        <td><strong>P90 Duration</strong></td>
                        <td>{pte.get('overall_p90_duration', 0):.2f} ms</td>
                    </tr>
                    <tr>
                        <td><strong>P95 Duration</strong></td>
                        <td>{pte.get('overall_p95_duration', 0):.2f} ms</td>
                    </tr>
                    <tr>
                        <td><strong>Slowest Endpoint</strong></td>
                        <td class="endpoint-name">{pte.get('slowest_endpoint', 'N/A')[:50]}</td>
                    </tr>
                </table>
            </div>
        </div>
        """
    
    def _duration_charts(self) -> str:
        """Duration comparison charts"""
        return """
        <div class="two-column">
            <div class="chart-container">
                <h2>Call Volume Comparison</h2>
                <div class="chart-wrapper">
                    <canvas id="callVolumeChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <h2>Response Time Comparison</h2>
                <div class="chart-wrapper">
                    <canvas id="durationChart"></canvas>
                </div>
            </div>
        </div>
        """
    
    def _endpoint_tables(self) -> str:
        """Top and slowest endpoints tables"""
        top_endpoints = self.report.get('top_volume_endpoints', [])[:10]
        slow_endpoints = self.report.get('slowest_endpoints', [])[:10]
        
        top_rows = ""
        for i, ep in enumerate(top_endpoints, 1):
            top_rows += f"""
            <tr>
                <td>{i}</td>
                <td class="endpoint-name">{ep['api_endpoint'][:60]}</td>
                <td>{ep['call_count']:,}</td>
                <td>{ep['avg_duration']:.2f} ms</td>
                <td>{ep.get('p95_duration', 0):.2f} ms</td>
            </tr>
            """
        
        slow_rows = ""
        for i, ep in enumerate(slow_endpoints, 1):
            slow_rows += f"""
            <tr>
                <td>{i}</td>
                <td class="endpoint-name">{ep['api_endpoint'][:60]}</td>
                <td>{ep.get('avg_duration', 0):.2f} ms</td>
                <td>{ep.get('p90_duration', 0):.2f} ms</td>
                <td>{ep.get('p95_duration', 0):.2f} ms</td>
            </tr>
            """
        
        return f"""
        <div class="two-column">
            <div class="chart-container">
                <h2>🔝 Top 10 Endpoints by Volume</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Endpoint</th>
                            <th>Total Calls</th>
                            <th>Avg Duration</th>
                            <th>P95 Duration</th>
                        </tr>
                    </thead>
                    <tbody>
                        {top_rows}
                    </tbody>
                </table>
            </div>
            
            <div class="chart-container">
                <h2>🐌 Top 10 Slowest Endpoints</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Endpoint</th>
                            <th>Avg Duration</th>
                            <th>P90</th>
                            <th>P95</th>
                        </tr>
                    </thead>
                    <tbody>
                        {slow_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    def _issues_table(self) -> str:
        """Critical issues table"""
        issues = self.report.get('critical_issues', [])[:20]
        
        if not issues:
            return """
            <div class="chart-container">
                <h2>✅ Critical Issues</h2>
                <p style="color: #38a169; font-size: 1.2em; padding: 20px;">
                    No critical issues found! All tests passed successfully.
                </p>
            </div>
            """
        
        rows = ""
        for issue in issues:
            rows += f"""
            <tr>
                <td class="endpoint-name">{issue['api_endpoint'][:50]}</td>
                <td>{issue['metric_name']}</td>
                <td>{issue['prod_value']:.2f}</td>
                <td>{issue['pte_value']:.2f}</td>
                <td>{issue['difference_pct']:+.1f}%</td>
                <td class="severity-{issue['severity']}">{issue['severity'].upper()}</td>
            </tr>
            """
        
        return f"""
        <div class="chart-container">
            <h2>⚠️ Critical & High Priority Issues</h2>
            <table>
                <thead>
                    <tr>
                        <th>Endpoint</th>
                        <th>Metric</th>
                        <th>Production</th>
                        <th>PTE</th>
                        <th>Difference</th>
                        <th>Severity</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """
    
    def _coverage_section(self) -> str:
        """Coverage and untested endpoints"""
        coverage = self.report['coverage']
        untested = coverage.get('untested_list', [])[:30]
        
        if not untested:
            return """
            <div class="chart-container">
                <h2>✅ Endpoint Coverage</h2>
                <p style="color: #38a169; font-size: 1.2em; padding: 20px;">
                    100% coverage! All production endpoints are tested in PTE.
                </p>
            </div>
            """
        
        items = ""
        for endpoint in untested:
            items += f'<div class="untested-item">{endpoint}</div>'
        
        return f"""
        <div class="chart-container">
            <h2>⚠️ Untested Endpoints ({len(untested)} total)</h2>
            <p style="color: #4a5568; margin-bottom: 15px;">
                The following endpoints are active in production but not tested in PTE:
            </p>
            <div class="untested-list">
                {items}
            </div>
        </div>
        """
    
    def _chart_scripts(self) -> str:
        """Generate Chart.js scripts"""
        prod = self.report['production_metrics']
        pte = self.report['pte_metrics']
        
        return f"""<script>
        Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        
        // Call Volume Chart
        new Chart(document.getElementById('callVolumeChart'), {{
            type: 'bar',
            data: {{
                labels: ['Total Calls', 'Avg per Endpoint'],
                datasets: [{{
                    label: 'Production',
                    data: [{prod.get('total_calls', 0)}, {prod.get('avg_call_count_per_endpoint', 0):.0f}],
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }}, {{
                    label: 'PTE',
                    data: [{pte.get('total_calls', 0)}, {pte.get('avg_call_count_per_endpoint', 0):.0f}],
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
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
        
        // Duration Chart
        new Chart(document.getElementById('durationChart'), {{
            type: 'bar',
            data: {{
                labels: ['Avg Duration', 'P90', 'P95'],
                datasets: [{{
                    label: 'Production',
                    data: [{prod.get('overall_avg_duration', 0):.2f}, {prod.get('overall_p90_duration', 0):.2f}, {prod.get('overall_p95_duration', 0):.2f}],
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }}, {{
                    label: 'PTE',
                    data: [{pte.get('overall_avg_duration', 0):.2f}, {pte.get('overall_p90_duration', 0):.2f}, {pte.get('overall_p95_duration', 0):.2f}],
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
                        title: {{ display: true, text: 'Duration (ms)' }}
                    }}
                }}
            }}
        }});
        </script>"""


# Main function to generate dashboard
def generate_custom_dashboard(report: Dict, output_file: str = None) -> str:
    """Generate HTML dashboard from custom analysis report"""
    dashboard = CustomHTMLDashboard(report)
    return dashboard.generate(output_file)


# Complete workflow example
if __name__ == "__main__":
    # Example: Complete workflow
    """
    from custom_oracle_analyzer import run_custom_analysis
    from custom_html_dashboard import generate_custom_dashboard
    
    db_config = {
        'username': 'your_username',
        'password': 'your_password',
        'dsn': 'hostname:1521/service_name'
    }
    
    # Run analysis
    report = run_custom_analysis(db_config, prod_days=7, pte_days=30)
    
    # Generate dashboard
    dashboard_file = generate_custom_dashboard(report)
    
    # Open in browser
    import webbrowser
    webbrowser.open(dashboard_file)
    """
    pass
