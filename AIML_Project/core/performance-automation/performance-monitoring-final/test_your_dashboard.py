#!/usr/bin/env python3
"""
Test script for your specific Kibana dashboard
"""
import argparse
import json
from fetchers.kibana_fetcher import KibanaDataFetcher
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(description='Test Your Kibana Dashboard')
    
    parser.add_argument('--kibana-url', required=True, help='Kibana URL')
    parser.add_argument('--kibana-user', required=True, help='Kibana username')
    parser.add_argument('--kibana-pass', required=True, help='Kibana password')
    
    # Your dashboard details
    parser.add_argument('--dashboard-id', 
                       default='d35dba6a7-2801-46b0-988e-2a7848b106e8',
                       help='Dashboard ID')
    
    # Field configuration
    parser.add_argument('--index-pattern', 
                       help='Index pattern (will auto-detect if not provided)')
    parser.add_argument('--endpoint-field', 
                       default='userRequestedUri.keyword',
                       help='Field containing API endpoint')
    parser.add_argument('--time-field', 
                       default='@timestamp',
                       help='Timestamp field')
    
    parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    logger = setup_logger('DashboardTest')
    
    logger.info("=" * 80)
    logger.info("Testing Your Kibana Dashboard")
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
    
    # Extract index pattern if not provided
    index_pattern = args.index_pattern
    if not index_pattern:
        logger.info("\n→ Auto-detecting index pattern from dashboard...")
        index_pattern = fetcher.extract_index_pattern_from_dashboard(args.dashboard_id)
        
        if index_pattern:
            logger.info(f"✓ Detected index pattern: {index_pattern}")
        else:
            logger.error("✗ Could not detect index pattern. Please provide --index-pattern")
            return 1
    
    # Fetch dashboard data
    logger.info("\n→ Fetching dashboard table data...")
    logger.info(f"   Dashboard ID: {args.dashboard_id}")
    logger.info(f"   Index Pattern: {index_pattern}")
    logger.info(f"   Endpoint Field: {args.endpoint_field}")
    logger.info(f"   Time Range: Last 5 minutes")
    
    api_metrics = fetcher.fetch_dashboard_table_data(
        index_pattern=index_pattern,
        endpoint_field=args.endpoint_field,
        time_field=args.time_field,
        time_range_minutes=5
    )
    
    if api_metrics:
        logger.info(f"\n✓ Successfully fetched data for {len(api_metrics)} API endpoints")
        
        # Display results in table format
        logger.info("\n" + "=" * 120)
        logger.info("API ENDPOINT METRICS")
        logger.info("=" * 120)
        
        header = f"{'API Endpoint':<50} {'Total':>8} {'Pass':>8} {'Fail':>8} {'Min':>8} {'Avg':>8} {'Max':>8} {'P90':>8} {'P95':>8}"
        logger.info(header)
        logger.info("-" * 120)
        
        for api in api_metrics[:20]:  # Show first 20
            row = (
                f"{api['api_endpoint'][:50]:<50} "
                f"{api['total_requests']:>8} "
                f"{api['pass_count']:>8} "
                f"{api['fail_count']:>8} "
                f"{api['min_response_time']:>8.2f} "
                f"{api['avg_response_time']:>8.2f} "
                f"{api['max_response_time']:>8.2f} "
                f"{api['p90_response_time']:>8.2f} "
                f"{api['p95_response_time']:>8.2f}"
            )
            logger.info(row)
        
        if len(api_metrics) > 20:
            logger.info(f"... and {len(api_metrics) - 20} more endpoints")
        
        logger.info("-" * 120)
        
        # Calculate totals
        total_requests = sum(api['total_requests'] for api in api_metrics)
        total_pass = sum(api['pass_count'] for api in api_metrics)
        total_fail = sum(api['fail_count'] for api in api_metrics)
        
        logger.info(f"{'TOTALS':<50} {total_requests:>8} {total_pass:>8} {total_fail:>8}")
        logger.info("=" * 120)
        
        # Save to file
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(api_metrics, f, indent=2)
            logger.info(f"\n✓ Data saved to: {args.output}")
        
        # Configuration for monitoring
        logger.info("\n" + "=" * 80)
        logger.info("CONFIGURATION FOR MONITORING")
        logger.info("=" * 80)
        logger.info("\nUse these parameters in your monitoring setup:")
        logger.info(f"  --kibana-index \"{index_pattern}\"")
        logger.info(f"  --kibana-endpoint-field \"{args.endpoint_field}\"")
        logger.info(f"  --kibana-time-field \"{args.time_field}\"")
        
    else:
        logger.warning("✗ No data returned")
        logger.info("\nTroubleshooting:")
        logger.info("1. Verify the index pattern is correct")
        logger.info("2. Check if data exists in the last 5 minutes")
        logger.info("3. Verify field names match your data")
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())