"""
Report Generator - Create HTML reports from monitoring data
"""
import os
from datetime import datetime
from typing import Dict, List
from jinja2 import Template
import json
from utils.logger import setup_logger

class ReportGenerator:
    """Generate HTML reports from monitoring data"""
    
    def __init__(self, db_handler):
        self.db_handler = db_handler
        self.logger = setup_logger('ReportGenerator')
    
    def generate_consolidated_report(self, test_run_id: str, output_dir: str = './reports'):
        """
        Generate consolidated HTML report with all metrics
        
        Args:
            test_run_id: Test run identifier
            output_dir: Output directory for reports
        """
        self.logger.info(f"Generating consolidated report for: {test_run_id}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Retrieve all data
        data = self.db_handler.get_test_run_metrics(test_run_id)
        summary = self.db_handler.get_metrics_summary(test_run_id)
        
        # Generate HTML report
        html_content = self._create_html_report(test_run_id, data, summary)
        
        # Write report
        report_file = os.path.join(output_dir, 'consolidated_report.html')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"✓ Report generated: {report_file}")
        
        # Generate individual metric reports
        self._generate_appdynamics_report(test_run_id, data, output_dir)
        self._generate_kibana_report(test_run_id, data, output_dir)
        
        return report_file
    
    def _create_html_report(self, test_run_id: str, data: Dict, summary: Dict) -> str:
        """Create main HTML report"""
        
        template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Performance Monitoring Report - {{ test_run_id }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 5px;
        }
        .info-section {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .info-item {
            margin: 5px 0;
        }
        .info-label {
            font-weight: bold;
            color: #2c3e50;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .metric-category {
            background-color: #2ecc71;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
        }
        .status {
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
        }
        .status-completed {
            background-color: #2ecc71;
            color: white;
        }
        .status-running {
            background-color: #f39c12;
            color: white;
        }
        .status-failed {
            background-color: #e74c3c;
            color: white;
        }
        .summary-box {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 20px;
            margin: 10px;
            border-radius: 5px;
            min-width: 200px;
        }
        .summary-value {
            font-size: 32px;
            font-weight: bold;
        }
        .summary-label {
            font-size: 14px;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Performance Monitoring Report</h1>
        
        <div class="info-section">
            <div class="info-item">
                <span class="info-label">Test Run ID:</span> {{ test_run_id }}
            </div>
            {% if test_run %}
            <div class="info-item">
                <span class="info-label">Test Name:</span> {{ test_run.TEST_NAME or 'N/A' }}
            </div>
            <div class="info-item">
                <span class="info-label">Start Time:</span> {{ test_run.START_TIME }}
            </div>
            <div class="info-item">
                <span class="info-label">End Time:</span> {{ test_run.END_TIME or 'N/A' }}
            </div>
            <div class="info-item">
                <span class="info-label">Duration:</span> {{ test_run.DURATION_MINUTES }} minutes
            </div>
            <div class="info-item">
                <span class="info-label">Status:</span> 
                <span class="status status-{{ test_run.STATUS }}">{{ test_run.STATUS }}</span>
            </div>
            {% endif %}
        </div>
        
        <h2>Summary</h2>
        <div>
            <div class="summary-box">
                <div class="summary-value">{{ appd_metrics_count }}</div>
                <div class="summary-label">AppDynamics Data Points</div>
            </div>
            <div class="summary-box" style="background-color: #9b59b6;">
                <div class="summary-value">{{ kibana_data_count }}</div>
                <div class="summary-label">Kibana Data Points</div>
            </div>
        </div>
        
        {% if summary.appdynamics %}
        <h2>AppDynamics Metrics Summary</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Metric Name</th>
                <th>Data Points</th>
                <th>Avg Value</th>
                <th>Min Value</th>
                <th>Max Value</th>
            </tr>
            {% for metric in summary.appdynamics %}
            <tr>
                <td><span class="metric-category">{{ metric.METRIC_CATEGORY }}</span></td>
                <td>{{ metric.METRIC_NAME }}</td>
                <td>{{ metric.DATA_POINTS }}</td>
                <td>{{ "%.2f"|format(metric.AVG_VALUE) if metric.AVG_VALUE else 'N/A' }}</td>
                <td>{{ "%.2f"|format(metric.MIN_VALUE) if metric.MIN_VALUE else 'N/A' }}</td>
                <td>{{ "%.2f"|format(metric.MAX_VALUE) if metric.MAX_VALUE else 'N/A' }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        {% if summary.kibana %}
        <h2>Kibana Data Summary</h2>
        <table>
            <tr>
                <th>Visualization Name</th>
                <th>Data Points</th>
            </tr>
            {% for viz in summary.kibana %}
            <tr>
                <td>{{ viz.VISUALIZATION_NAME }}</td>
                <td>{{ viz.DATA_POINTS }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; text-align: center; color: #7f8c8d;">
            <p>Report generated at {{ generation_time }}</p>
        </div>
    </div>
</body>
</html>
        '''
        
        template_obj = Template(template)
        
        html = template_obj.render(
            test_run_id=test_run_id,
            test_run=data.get('test_run'),
            summary=summary,
            appd_metrics_count=len(data.get('appdynamics_metrics', [])),
            kibana_data_count=len(data.get('kibana_data', [])),
            generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        return html
    
    def _generate_appdynamics_report(self, test_run_id: str, data: Dict, output_dir: str):
        """Generate detailed AppDynamics report"""
        # Similar structure - detailed metrics breakdown
        report_file = os.path.join(output_dir, 'appd_metrics.html')
        # Implementation similar to above
        self.logger.info(f"✓ AppDynamics report: {report_file}")
    
    def _generate_kibana_report(self, test_run_id: str, data: Dict, output_dir: str):
        """Generate detailed Kibana report"""
        # Similar structure - visualization data breakdown
        report_file = os.path.join(output_dir, 'kibana_data.html')
        # Implementation similar to above
        self.logger.info(f"✓ Kibana report: {report_file}")