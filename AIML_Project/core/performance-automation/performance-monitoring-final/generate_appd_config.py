#!/usr/bin/env python3
"""
Generate AppDynamics configuration file - Filter by Active Nodes Only
Only includes nodes with App Agent availability > 0%
"""
import argparse
import json
import sys
from datetime import datetime
from fetchers.appdynamics_fetcher import AppDynamicsDataFetcher
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(
        description='Generate AppDynamics configuration from application names (Active Nodes Only)'
    )
    
    # AppDynamics credentials
    parser.add_argument('--controller', required=True, help='AppDynamics controller URL')
    parser.add_argument('--account', required=True, help='AppDynamics account name')
    parser.add_argument('--username', required=True, help='AppDynamics username')
    parser.add_argument('--password', required=True, help='AppDynamics password')
    
    # Application names
    parser.add_argument('--app-names', required=True, 
                       help='Comma-separated list of application names')
    
    # Filtering options
    parser.add_argument('--min-availability', type=float, default=1.0,
                       help='Minimum app agent availability percentage (default: 1.0 = 1%%)')
    parser.add_argument('--check-last-minutes', type=int, default=15,
                       help='Check node availability in last N minutes (default: 15)')
    parser.add_argument('--include-inactive-tiers', action='store_true',
                       help='Include tiers even if they have no active nodes')
    
    # Output
    parser.add_argument('--output', required=True, 
                       help='Output JSON configuration file path')
    
    # Verbose
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed filtering information')
    
    args = parser.parse_args()
    
    # Setup logger
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger('AppDConfigGenerator', level=log_level)
    
    logger.info("=" * 80)
    logger.info("AppDynamics Configuration Generator (Active Nodes Filter)")
    logger.info("=" * 80)
    logger.info(f"Minimum App Agent Availability: {args.min_availability}%")
    logger.info(f"Checking availability in last: {args.check_last_minutes} minutes")
    logger.info("=" * 80)
    
    # Parse application names
    app_names = [name.strip() for name in args.app_names.split(',')]
    logger.info(f"\nApplications to process: {len(app_names)}")
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
    logger.info("GENERATING CONFIGURATION WITH NODE FILTERING")
    logger.info("=" * 80)
    
    config = {
        'description': 'AppDynamics monitoring configuration (Active nodes only)',
        'generated_at': datetime.now().isoformat(),
        'filter_criteria': {
            'min_availability_percent': args.min_availability,
            'check_period_minutes': args.check_last_minutes
        },
        'applications': []
    }
    
    total_tiers = 0
    total_nodes = 0
    total_inactive_nodes = 0
    total_active_nodes = 0
    
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
            logger.info(f"\n  [{tier_idx}/{len(tiers)}] {tier_name}")
            
            # Get all nodes for tier
            all_nodes = fetcher.get_nodes_for_tier(app_name, tier_name)
            
            if not all_nodes:
                logger.info(f"      No nodes found")
                if args.include_inactive_tiers:
                    app_config['tiers'].append({
                        'tier_name': tier_name,
                        'nodes': []
                    })
                    total_tiers += 1
                continue
            
            logger.info(f"      Total nodes discovered: {len(all_nodes)}")
            
            # Filter nodes by availability
            active_nodes = []
            inactive_nodes = []
            
            for node in all_nodes:
                node_name = node.get('name')
                node_id = node.get('id')
                
                # Check node health/availability
                is_active = fetcher.check_node_availability(
                    app_name=app_name,
                    node_id=node_id,
                    min_availability=args.min_availability,
                    duration_mins=args.check_last_minutes
                )
                
                if is_active:
                    active_nodes.append(node_name)
                    logger.info(f"      ✓ {node_name} - ACTIVE")
                else:
                    inactive_nodes.append(node_name)
                    if args.verbose:
                        logger.debug(f"      ✗ {node_name} - INACTIVE (filtered out)")
            
            # Summary for this tier
            logger.info(f"\n      Active nodes: {len(active_nodes)}/{len(all_nodes)}")
            if inactive_nodes:
                logger.info(f"      Filtered out: {len(inactive_nodes)} inactive nodes")
            
            total_nodes += len(all_nodes)
            total_active_nodes += len(active_nodes)
            total_inactive_nodes += len(inactive_nodes)
            
            # Add tier to config only if it has active nodes OR if include_inactive_tiers is True
            if active_nodes or args.include_inactive_tiers:
                app_config['tiers'].append({
                    'tier_name': tier_name,
                    'nodes': active_nodes
                })
                total_tiers += 1
            else:
                logger.warning(f"      ⚠ Tier '{tier_name}' excluded (no active nodes)")
        
        if app_config['tiers']:
            config['applications'].append(app_config)
    
    # Save configuration
    logger.info("\n→ Saving configuration...")
    try:
        with open(args.output, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✓ Saved to: {args.output}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("GENERATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Applications: {len(config['applications'])}")
        logger.info(f"Total Tiers: {total_tiers}")
        logger.info(f"Total Nodes Discovered: {total_nodes}")
        logger.info(f"  ✓ Active Nodes (included): {total_active_nodes}")
        logger.info(f"  ✗ Inactive Nodes (filtered): {total_inactive_nodes}")
        
        if total_nodes > 0:
            active_percentage = (total_active_nodes / total_nodes) * 100
            logger.info(f"  Active Percentage: {active_percentage:.1f}%")
        
        logger.info("=" * 80)
        
        # Show configuration preview
        logger.info("\nConfiguration Preview:")
        logger.info("-" * 80)
        for app in config['applications']:
            logger.info(f"\nApplication: {app['app_name']}")
            for tier in app['tiers']:
                logger.info(f"  Tier: {tier['tier_name']} ({len(tier['nodes'])} active nodes)")
                if args.verbose and tier['nodes']:
                    for node in tier['nodes'][:5]:
                        logger.info(f"    - {node}")
                    if len(tier['nodes']) > 5:
                        logger.info(f"    ... and {len(tier['nodes']) - 5} more")
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ Error saving: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())