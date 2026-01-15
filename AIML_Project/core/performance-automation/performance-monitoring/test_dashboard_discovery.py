#!/usr/bin/env python3
"""
Test script to discover and display dashboard configuration
"""
import argparse
import json
from fetchers.appdynamics_fetcher import AppDynamicsDataFetcher
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(description='Test AppDynamics Dashboard Discovery')
    parser.add_argument('--controller', required=True, help='Controller URL')
    parser.add_argument('--account', required=True, help='Account name')
    parser.add_argument('--username', required=True, help='Username')
    parser.add_argument('--password', required=True, help='Password')
    parser.add_argument('--dashboard-id', type=int, required=True, help='Dashboard ID')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger('DashboardDiscovery', level=log_level)
    
    # Initialize fetcher
    fetcher = AppDynamicsDataFetcher(
        controller_url=args.controller,
        account_name=args.account,
        username=args.username,
        password=args.password
    )
    
    # Test connection
    if not fetcher.test_connection():
        logger.error("Connection test failed!")
        return 1
    
    # Get raw dashboard data
    logger.info(f"\nFetching raw dashboard data...")
    raw_dashboard = fetcher.get_dashboard_details(args.dashboard_id)
    
    if args.verbose and raw_dashboard:
        logger.info("\nRaw Dashboard Structure:")
        logger.info(json.dumps(raw_dashboard, indent=2)[:2000] + "...")  # First 2000 chars
    
    # Parse dashboard
    logger.info(f"\nParsing Dashboard ID: {args.dashboard_id}")
    widget_configs = fetcher.parse_dashboard_to_config(args.dashboard_id)
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("DISCOVERED WIDGETS:")
    logger.info("=" * 80)
    
    for idx, widget in enumerate(widget_configs, 1):
        logger.info(f"\n[{idx}] {widget['widget_name']}")
        logger.info(f"    Widget Type: {widget['widget_type']}")
        logger.info(f"    Metric Type: {widget['metric_type']}")
        logger.info(f"    Apps/Tiers/Nodes: {len(widget.get('apps_tiers_nodes', []))}")
        
        for metric_info in widget.get('apps_tiers_nodes', []):
            logger.info(f"    - App: {metric_info.get('app_name')}")
            logger.info(f"      Tier: {metric_info.get('tier_name', 'N/A')}")
            logger.info(f"      Node: {metric_info.get('node_name', 'TIER_LEVEL')}")
            logger.info(f"      Category: {metric_info.get('metric_category')}")
            if args.verbose:
                logger.info(f"      Metric Path: {metric_info.get('metric_path', 'N/A')}")
    
    # Save to file if requested
    if args.output:
        output_data = {
            'dashboard_id': args.dashboard_id,
            'total_widgets': len(widget_configs),
            'widgets': widget_configs,
            'raw_dashboard': raw_dashboard if args.verbose else None
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"\n✓ Configuration saved to: {args.output}")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"Total Widgets Discovered: {len(widget_configs)}")
    logger.info("=" * 80)
    
    return 0

if __name__ == '__main__':
    exit(main())