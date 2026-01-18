#!/usr/bin/env python3
"""
Generate AppDynamics configuration file containing apps, tiers, and nodes
"""
import argparse
import json
import sys
from datetime import datetime
from fetchers.appdynamics_fetcher import AppDynamicsDataFetcher
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(
        description='Generate AppDynamics configuration from application names'
    )
    
    # AppDynamics credentials
    parser.add_argument('--controller', required=True, help='AppDynamics controller URL')
    parser.add_argument('--account', required=True, help='AppDynamics account name')
    parser.add_argument('--username', required=True, help='AppDynamics username')
    parser.add_argument('--password', required=True, help='AppDynamics password')
    
    # Application names
    parser.add_argument('--app-names', required=True, 
                       help='Comma-separated list of application names')
    
    # Output
    parser.add_argument('--output', required=True, 
                       help='Output JSON configuration file path')
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger('AppDConfigGenerator')
    
    logger.info("=" * 80)
    logger.info("AppDynamics Configuration Generator")
    logger.info("=" * 80)
    
    # Parse application names
    app_names = [name.strip() for name in args.app_names.split(',')]
    logger.info(f"Applications to process: {len(app_names)}")
    for app in app_names:
        logger.info(f"  - {app}")
    
    # Initialize fetcher
    logger.info("\n→ Connecting to AppDynamics...")
    fetcher = AppDynamicsDataFetcher(
        controller_url=args.controller,
        account_name=args.account,
        username=args.username,
        password=args.password
    )
    
    if not fetcher.test_connection():
        logger.error("✗ Connection failed!")
        return 1
    
    # Validate applications exist
    logger.info("\n→ Validating applications...")
    all_apps = fetcher.get_applications()
    if not all_apps:
        logger.error("✗ Could not fetch applications!")
        return 1
    
    available_app_names = [app.get('name') for app in all_apps]
    
    invalid_apps = [app for app in app_names if app not in available_app_names]
    if invalid_apps:
        logger.error(f"\n✗ Invalid application names: {', '.join(invalid_apps)}")
        logger.error(f"Available: {', '.join(available_app_names)}")
        return 1
    
    # Generate configuration
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING CONFIGURATION")
    logger.info("=" * 80)
    
    config = {
        'description': 'AppDynamics monitoring configuration',
        'generated_at': datetime.now().isoformat(),
        'applications': []
    }
    
    total_tiers = 0
    total_nodes = 0
    
    for app_idx, app_name in enumerate(app_names, 1):
        logger.info(f"\n[{app_idx}/{len(app_names)}] {app_name}")
        logger.info("-" * 80)
        
        tiers = fetcher.get_tiers_for_application(app_name)
        if not tiers:
            logger.warning(f"  No tiers found")
            continue
        
        logger.info(f"  Found {len(tiers)} tiers")
        
        app_config = {
            'app_name': app_name,
            'tiers': []
        }
        
        for tier_idx, tier in enumerate(tiers, 1):
            tier_name = tier.get('name')
            logger.info(f"  [{tier_idx}/{len(tiers)}] {tier_name}")
            
            nodes = fetcher.get_nodes_for_tier(app_name, tier_name)
            node_names = []
            
            if nodes:
                node_names = [node.get('name') for node in nodes]
                for node_name in node_names:
                    logger.info(f"      - {node_name}")
                total_nodes += len(node_names)
            else:
                logger.info(f"      No nodes (tier-level only)")
            
            app_config['tiers'].append({
                'tier_name': tier_name,
                'nodes': node_names
            })
            total_tiers += 1
        
        config['applications'].append(app_config)
    
    # Save configuration
    logger.info("\n→ Saving configuration...")
    try:
        with open(args.output, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✓ Saved to: {args.output}")
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Applications: {len(config['applications'])}")
        logger.info(f"Total Tiers: {total_tiers}")
        logger.info(f"Total Nodes: {total_nodes}")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ Error saving: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())