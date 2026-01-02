#!/usr/bin/env python3
"""
Performance Test Results Analyzer
Parses and analyzes Performance Center test results
"""

import argparse
import json
import os
import sys
from datetime import datetime
import pandas as pd
from pathlib import Path


class ResultsAnalyzer:
    """Analyze Performance Center test results"""
    
    def __init__(self, results_dir):
        self.results_dir = results_dir
        self.summary_data = {}
        self.transactions = []
        self.sla_results = []
        
    def parse_metadata(self, run_id):
        """Parse run metadata"""
        print("Parsing test metadata...")
        
        metadata_file = os.path.join(self.results_dir, f"metadata_{run_id}.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            self.summary_data = {
                'run_id': run_id,
                'test_name': metadata.get('testName', 'N/A'),
                'status': metadata.get('status', 'N/A'),
                'start_time': metadata.get('startTime', 'N/A'),
                'end_time': metadata.get('endTime', 'N/A'),
                'duration': metadata.get('duration', 'N/A')
            }
            
            print("✓ Metadata parsed")
        else:
            print("⚠ Metadata file not found, using defaults")
            self.summary_data = {
                'run_id': run_id,
                'test_name': 'Unknown',
                'status': 'Unknown'
            }
    
    def generate_mock_data(self):
        """Generate mock transaction data for demo"""
        print("Generating sample performance data...")
        
        # Mock transaction data
        self.transactions = [
            {
                'name': 'Login',
                'count': 1500,
                'passed': 1485,
                'failed': 15,
                'min': 0.25,
                'max': 3.45,
                'avg': 0.85,
                'percentile_90': 1.20,
                'percentile_95': 1.55,
                'std_dev': 0.35
            },
            {
                'name': 'Search',
                'count': 5000,
                'passed': 4950,
                'failed': 50,
                'min': 0.15,
                'max': 5.20,
                'avg': 1.25,
                'percentile_90': 2.10,
                'percentile_95': 2.85,
                'std_dev': 0.65
            },
            {
                'name': 'Add_to_Cart',
                'count': 3500,
                'passed': 3480,
                'failed': 20,
                'min': 0.30,
                'max': 4.10,
                'avg': 1.10,
                'percentile_90': 1.85,
                'percentile_95': 2.35,
                'std_dev': 0.55
            },
            {
                'name': 'Checkout',
                'count': 2000,
                'passed': 1970,
                'failed': 30,
                'min': 0.50,
                'max': 6.50,
                'avg': 2.35,
                'percentile_90': 3.95,
                'percentile_95': 4.75,
                'std_dev': 1.15
            },
            {
                'name': 'Logout',
                'count': 1500,
                'passed': 1495,
                'failed': 5,
                'min': 0.10,
                'max': 1.25,
                'avg': 0.45,
                'percentile_90': 0.75,
                'percentile_95': 0.95,
                'std_dev': 0.20
            }
        ]
        
        # Mock SLA results
        self.sla_results = [
            {
                'name': 'Average Response Time',
                'measurement': 'Transaction Response Time',
                'goal_value': 2.0,
                'actual_value': 1.20,
                'status': 'PASSED'
            },
            {
                'name': '90th Percentile Response',
                'measurement': 'Transaction Response Time',
                'goal_value': 3.0,
                'actual_value': 2.17,
                'status': 'PASSED'
            },
            {
                'name': 'Error Rate',
                'measurement': 'Failed Transactions %',
                'goal_value': 2.0,
                'actual_value': 0.86,
                'status': 'PASSED'
            },
            {
                'name': 'Throughput',
                'measurement': 'Transactions per second',
                'goal_value': 100,
                'actual_value': 185,
                'status': 'PASSED'
            }
        ]
        
        print("✓ Sample data generated")
    
    def calculate_statistics(self):
        """Calculate overall statistics"""
        print("Calculating statistics...")
        
        total_count = sum(t['count'] for t in self.transactions)
        total_passed = sum(t['passed'] for t in self.transactions)
        total_failed = sum(t['failed'] for t in self.transactions)
        
        weighted_avg = sum(t['avg'] * t['count'] for t in self.transactions) / total_count
        
        self.summary_data.update({
            'total_transactions': total_count,
            'passed_transactions': total_passed,
            'failed_transactions': total_failed,
            'success_rate': round((total_passed / total_count) * 100, 2),
            'failure_rate': round((total_failed / total_count) * 100, 2),
            'avg_response_time': round(weighted_avg, 2),
            'sla_passed': all(sla['status'] == 'PASSED' for sla in self.sla_results)
        })
        
        print("✓ Statistics calculated")
    
    def create_excel_report(self, output_file):
        """Create Excel report with multiple sheets"""
        print(f"Creating Excel report: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = pd.DataFrame([self.summary_data])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Transactions sheet
            transactions_df = pd.DataFrame(self.transactions)
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # SLA sheet
            sla_df = pd.DataFrame(self.sla_results)
            sla_df.to_excel(writer, sheet_name='SLA_Results', index=False)
        
        print(f"✓ Excel report created: {output_file}")
    
    def create_html_report(self, output_file, test_name, build_number):
        """Create comprehensive HTML report"""
        print(f"Creating HTML report: {output_file}")
        
        # Calculate pass/fail for styling
        sla_status_color = 'green' if self.summary_data.get('sla_passed') else 'red'
        sla_status_text = 'PASSED' if self.summary_data.get('sla_passed') else 'FAILED'
        
        # Build transactions table
        transactions_html = ""
        for txn in self.transactions:
            success_rate = (txn['passed'] / txn['count']) * 100
            row_color = '#f8f9fa' if success_rate >= 99 else '#fff3cd'
            
            transactions_html += f"""
            <tr style="background-color: {row_color}">
                <td>{txn['name']}</td>
                <td>{txn['count']:,}</td>
                <td style="color: green; font-weight: bold">{txn['passed']:,}</td>
                <td style="color: red; font-weight: bold">{txn['failed']:,}</td>
                <td>{success_rate:.2f}%</td>
                <td>{txn['min']:.2f}s</td>
                <td>{txn['avg']:.2f}s</td>
                <td>{txn['percentile_90']:.2f}s</td>
                <td>{txn['percentile_95']:.2f}s</td>
                <td>{txn['max']:.2f}s</td>
            </tr>
            """
        
        # Build SLA table
        sla_html = ""
        for sla in self.sla_results:
            status_color = 'green' if sla['status'] == 'PASSED' else 'red'
            status_icon = '✓' if sla['status'] == 'PASSED' else '✗'
            
            sla_html += f"""
            <tr>
                <td>{sla['name']}</td>
                <td>{sla['measurement']}</td>
                <td>{sla['goal_value']}</td>
                <td>{sla['actual_value']}</td>
                <td style="color: {status_color}; font-weight: bold">{status_icon} {sla['status']}</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Test Report - {test_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    border-bottom: 3px solid #007bff;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #555;
                    margin-top: 30px;
                    border-bottom: 2px solid #ddd;
                    padding-bottom: 8px;
                }}
                .header-info {{
                    background-color: #e9ecef;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .summary-card {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 4px solid #007bff;
                }}
                .summary-card h3 {{
                    margin: 0 0 10px 0;
                    color: #666;
                    font-size: 14px;
                    text-transform: uppercase;
                }}
                .summary-card .value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                }}
                .sla-status {{
                    font-size: 32px;
                    font-weight: bold;
                    color: {sla_status_color};
                    text-align: center;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background-color: #007bff;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                tr:hover {{
                    background-color: #f1f3f5;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 12px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 Performance Test Report</h1>
                
                <div class="header-info">
                    <strong>Test Name:</strong> {test_name}<br>
                    <strong>Build Number:</strong> {build_number}<br>
                    <strong>Run ID:</strong> {self.summary_data.get('run_id', 'N/A')}<br>
                    <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                
                <h2>📊 Overall SLA Status</h2>
                <div class="sla-status">
                    {sla_status_text}
                </div>
                
                <h2>📈 Executive Summary</h2>
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>Total Transactions</h3>
                        <div class="value">{self.summary_data.get('total_transactions', 0):,}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Success Rate</h3>
                        <div class="value" style="color: green">{self.summary_data.get('success_rate', 0)}%</div>
                    </div>
                    <div class="summary-card">
                        <h3>Failed Transactions</h3>
                        <div class="value" style="color: red">{self.summary_data.get('failed_transactions', 0):,}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Avg Response Time</h3>
                        <div class="value">{self.summary_data.get('avg_response_time', 0)}s</div>
                    </div>
                </div>
                
                <h2>📋 SLA Results</h2>
                <table>
                    <thead>
                        <tr>
                            <th>SLA Name</th>
                            <th>Measurement</th>
                            <th>Goal Value</th>
                            <th>Actual Value</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sla_html}
                    </tbody>
                </table>
                
                <h2>🔄 Transaction Details</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Transaction Name</th>
                            <th>Total</th>
                            <th>Passed</th>
                            <th>Failed</th>
                            <th>Success Rate</th>
                            <th>Min (s)</th>
                            <th>Avg (s)</th>
                            <th>90th % (s)</th>
                            <th>95th % (s)</th>
                            <th>Max (s)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {transactions_html}
                    </tbody>
                </table>
                
                <div class="footer">
                    <p>Report generated by Performance Center Automation Pipeline</p>
                    <p>© {datetime.now().year} - Automated Performance Testing</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"✓ HTML report created: {output_file}")


def analyze_command(args):
    """Handle analyze command"""
    analyzer = ResultsAnalyzer(args.results_dir)
    
    # Parse metadata
    analyzer.parse_metadata(args.run_id)
    
    # Generate mock data (in real scenario, parse actual PC results)
    analyzer.generate_mock_data()
    
    # Calculate statistics
    analyzer.calculate_statistics()
    
    # Save JSON summary
    print(f"Saving analysis summary to: {args.output_json}")
    with open(args.output_json, 'w') as f:
        json.dump(analyzer.summary_data, f, indent=2)
    
    # Create Excel report
    analyzer.create_excel_report(args.output_excel)
    
    # Create HTML report
    with open(args.output_html, 'w') as f:
        f.write("<h1>Analysis Report</h1><p>Basic report - see final report for details</p>")
    
    print("✓ Analysis completed successfully!")


def report_command(args):
    """Handle report generation command"""
    analyzer = ResultsAnalyzer(args.results_dir)
    
    # Parse metadata
    analyzer.parse_metadata(args.run_id)
    
    # Generate mock data
    analyzer.generate_mock_data()
    
    # Calculate statistics
    analyzer.calculate_statistics()
    
    # Create comprehensive HTML report
    analyzer.create_html_report(args.output, args.test_name, args.build_number)
    
    print("✓ Report generation completed successfully!")


def main():
    parser = argparse.ArgumentParser(description='Performance Test Results Analyzer')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze test results')
    analyze_parser.add_argument('--results-dir', required=True)
    analyze_parser.add_argument('--run-id', required=True)
    analyze_parser.add_argument('--output-html', required=True)
    analyze_parser.add_argument('--output-json', required=True)
    analyze_parser.add_argument('--output-excel', required=True)
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate final report')
    report_parser.add_argument('--results-dir', required=True)
    report_parser.add_argument('--run-id', required=True)
    report_parser.add_argument('--test-name', required=True)
    report_parser.add_argument('--build-number', required=True)
    report_parser.add_argument('--output', required=True)
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        analyze_command(args)
    elif args.command == 'report':
        report_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()