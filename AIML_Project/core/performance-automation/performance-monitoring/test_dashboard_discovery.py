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
    
    args = parser.parse_args()
    
    logger = setup_logger('DashboardDiscovery')
    
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
    
    # Parse dashboard
    logger.info(f"Parsing Dashboard ID: {args.dashboard_id}")
    widget_configs = fetcher.parse_dashboard_to_config(args.dashboard_id)
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("DISCOVERED WIDGETS:")
    logger.info("=" * 80)
    
    for idx, widget in enumerate(widget_configs, 1):
        logger.info(f"\n[{idx}] {widget['widget_name']}")
        logger.info(f"    Type: {widget['metric_type']}")
        
        for metric_info in widget.get('apps_tiers_nodes', []):
            logger.info(f"    - App: {metric_info.get('app_name')}")
            logger.info(f"      Tier: {metric_info.get('tier_name')}")
            logger.info(f"      Node: {metric_info.get('node_name', 'TIER_LEVEL')}")
            logger.info(f"      Category: {metric_info.get('metric_category')}")
    
    # Save to file if requested
    if args.output:
        output_data = {
            'dashboard_id': args.dashboard_id,
            'total_widgets': len(widget_configs),
            'widgets': widget_configs
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"\n✓ Configuration saved to: {args.output}")
    
    return 0

if __name__ == '__main__':
    exit(main())