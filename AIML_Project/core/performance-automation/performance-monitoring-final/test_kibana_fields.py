#!/usr/bin/env python3
"""
Comprehensive Kibana field discovery and testing
"""
import argparse
import sys
from fetchers.kibana_fetcher import KibanaDataFetcher
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(description='Kibana Field Discovery and Testing')
    
    # Kibana credentials
    parser.add_argument('--kibana-url', required=True, help='Kibana URL')
    parser.add_argument('--kibana-user', required=True, help='Kibana username')
    parser.add_argument('--kibana-pass', required=True, help='Kibana password')
    
    # Actions
    parser.add_argument('--dashboard-id', help='Dashboard ID to analyze')
    parser.add_argument('--index-pattern', help='Index pattern to analyze fields')
    
    # Test query
    parser.add_argument('--test-query', action='store_true', help='Test query with field names')
    parser.add_argument('--api-field', default='api_name.keyword', help='API field name')
    parser.add_argument('--status-field', default='status', help='Status field name')
    parser.add_argument('--response-field', default='response_time', help='Response time field name')
    parser.add_argument('--time-field', default='@timestamp', help='Timestamp field name')
    
    # Output
    parser.add_argument('--output', help='Output file for dashboard JSON')
    
    args = parser.parse_args()
    
    logger = setup_logger('KibanaFieldTest')
    
    logger.info("=" * 80)
    logger.info("Kibana Field Discovery Tool")
    logger.info("=" * 80)
    
    # Initialize fetcher
    fetcher = KibanaDataFetcher(
        kibana_url=args.kibana_url,
        username=args.kibana_user,
        password=args.kibana_pass
    )
    
    if not fetcher.test_connection():
        logger.error("✗ Connection failed!")
        return 1
    
    # Analyze dashboard structure
    if args.dashboard_id:
        logger.info("\n→ Analyzing dashboard structure...")
        fetcher.print_dashboard_structure(
            dashboard_id=args.dashboard_id,
            output_file=args.output
        )
    
    # Analyze index fields
    if args.index_pattern:
        logger.info("\n→ Analyzing index fields...")
        fetcher.analyze_index_fields(args.index_pattern)
    
    # Test query with specified fields
    if args.test_query and args.index_pattern:
        logger.info("\n→ Testing query with specified fields...")
        fetcher.test_query_with_fields(
            index_pattern=args.index_pattern,
            api_field=args.api_field,
            status_field=args.status_field,
            response_field=args.response_field,
            time_field=args.time_field
        )
    
    logger.info("\n" + "=" * 80)
    logger.info("✓ ANALYSIS COMPLETE")
    logger.info("=" * 80)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())