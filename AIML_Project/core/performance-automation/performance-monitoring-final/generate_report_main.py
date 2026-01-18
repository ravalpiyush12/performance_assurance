#!/usr/bin/env python3
"""
Generate consolidated HTML reports from Oracle database
"""
import argparse
import sys
import os
from database.db_handler import MonitoringDataDB
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(description='Generate Monitoring Reports')
    parser.add_argument('--run-id', required=True, help='Test Run ID')
    parser.add_argument('--db-user', required=True, help='Oracle username')
    parser.add_argument('--db-pass', required=True, help='Oracle password')
    parser.add_argument('--db-dsn', required=True, help='Oracle DSN')
    parser.add_argument('--output-dir', default='./reports', help='Output directory')
    
    args = parser.parse_args()
    logger = setup_logger('ReportGeneration')
    
    try:
        logger.info(f"Generating reports for Test Run: {args.run_id}")
        
        # Connect to database
        db_handler = MonitoringDataDB(
            username=args.db_user,
            password=args.db_pass,
            dsn=args.db_dsn
        )
        
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Generate simple HTML report
        report_file = os.path.join(args.output_dir, 'consolidated_report.html')
        
        html_content = f"""
        <html>
        <head>
            <title>Performance Test Report - {args.run_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                .info {{ background-color: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Performance Monitoring Report</h1>
            <div class="info">
                <h2>Test Run ID: {args.run_id}</h2>
                <p>Report generated successfully.</p>
                <p>Query the following tables in Oracle for detailed metrics:</p>
                <ul>
                    <li>TEST_RUNS</li>
                    <li>APPD_SERVER_METRICS</li>
                    <li>APPD_JVM_METRICS</li>
                    <li>APPD_APPLICATION_METRICS</li>
                    <li>KIBANA_API_METRICS</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"✓ Report generated: {report_file}")
        return 0
        
    except Exception as e:
        logger.error(f"Error generating reports: {e}", exc_info=True)
        return 1
    finally:
        if 'db_handler' in locals():
            db_handler.close()

if __name__ == '__main__':
    sys.exit(main())
