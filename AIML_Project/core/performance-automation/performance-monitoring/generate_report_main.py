#!/usr/bin/env python3
"""
Generate reports from collected monitoring data
"""
import argparse
import sys
from database.db_handler import MonitoringDataDB
from reports.report_generator import ReportGenerator
from utils.logger import setup_logger

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate Monitoring Reports')
    parser.add_argument('--run-id', required=True, help='Test Run ID')
    parser.add_argument('--db-user', required=True, help='Oracle username')
    parser.add_argument('--db-pass', required=True, help='Oracle password')
    parser.add_argument('--db-dsn', required=True, help='Oracle DSN')
    parser.add_argument('--output-dir', default='./reports', help='Output directory')
    return parser.parse_args()

def main():
    args = parse_arguments()
    logger = setup_logger('ReportGeneration')
    
    try:
        logger.info(f"Generating reports for Test Run: {args.run_id}")
        
        # Connect to database
        db_handler = MonitoringDataDB(
            username=args.db_user,
            password=args.db_pass,
            dsn=args.db_dsn
        )
        
        # Generate reports
        report_gen = ReportGenerator(db_handler)
        report_file = report_gen.generate_consolidated_report(
            test_run_id=args.run_id,
            output_dir=args.output_dir
        )
        
        logger.info(f"✓ Reports generated successfully: {report_file}")
        return 0
        
    except Exception as e:
        logger.error(f"Error generating reports: {e}", exc_info=True)
        return 1
    finally:
        if 'db_handler' in locals():
            db_handler.close()

if __name__ == '__main__':
    sys.exit(main())