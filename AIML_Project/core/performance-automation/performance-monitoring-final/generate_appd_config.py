#!/usr/bin/env python3
"""
Generate AppDynamics configuration - Filter by App Agent Availability %
Only includes nodes with App Agent Availability >= threshold (default 50%)
"""
import argparse
import json
import sys
from datetime import datetime
from fetchers.appdynamics_fetcher import AppDynamicsDataFetcher
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(
        description='Generate AppDynamics config filtering by App Agent Availability %'
    )
    
    # AppDynamics credentials
    parser.add_argument('--controller', required=True, help='Controller URL')
    parser.add_argument('--account', required=True, help='Account name')
    parser.add_argument('--username', required=True, help='Username')
    parser.add_argument('--password', required=True, help='Password')
    
    # Application names
    parser.add_argument('--app-names', required=True, 
                       help='Comma-separated application names')
    
    # Filtering options
    parser.add_argument('--min-availability', type=float, default=50.0,
                       help='Minimum App Agent Availability %% (default: 50)')
    parser.add_argument('--check-duration', type=int, default=15,
                       help='Check availability over last N minutes (default: 15)')
    
    # Output
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--show-availability', action='store_true',
                       help='Show availability percentage for each node')
    
    args = parser.parse_args()
    
    # Setup logger
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger('AppDConfigGenerator', level=log_level)
    
    logger.info("=" * 80)
    logger.info("AppDynamics Config Generator - App Agent Availability Filter")
    logger.info("=" * 80)
    logger.info(f"Minimum Availability: {args.min_availability}%")
    logger.info(f"Check Period: {args.check_duration} minutes")
    logger.info("=" * 80)
    
    # Parse app names
    app_names = [name.strip() for name in args.app_names.split(',')]
    logger.info(f"\nApplications to process: {len(app_names)}")
    
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
    
    # Validate applications
    logger.info("\n→ Validating applications...")
    all_apps = fetcher.get_applications()
    if not all_apps:
        logger.error("✗ Could not fetch applications!")
        return 1
    
    available_app_names = [app.get('name') for app in all_apps]
    invalid_apps = [app for app in app_names if app not in available_app_names]
    
    if invalid_apps:
        logger.error(f"\n✗ Invalid apps: {', '.join(invalid_apps)}")
        return 1
    
    # Generate configuration
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING CONFIGURATION")
    logger.info("=" * 80)
    
    config = {
        'description': f'AppDynamics config - Nodes with availability >= {args.min_availability}%',
        'generated_at': datetime.now().isoformat(),
        'filter_criteria': {
            'min_availability_percent': args.min_availability,
            'check_period_minutes': args.check_duration
        },
        'applications': []
    }
    
    # Statistics
    stats = {
        'total_tiers': 0,
        'total_nodes_discovered': 0,
        'total_nodes_active': 0,
        'total_nodes_inactive': 0,
        'apps_processed': 0,
        'tiers_with_active_nodes': 0
    }
    
    for app_idx, app_name in enumerate(app_names, 1):
        logger.info(f"\n{'=' * 80}")
        logger.info(f"[{app_idx}/{len(app_names)}] Processing: {app_name}")
        logger.info(f"{'=' * 80}")
        
        tiers = fetcher.get_tiers_for_application(app_name)
        if not tiers:
            logger.warning(f"No tiers found for {app_name}")
            continue
        
        logger.info(f"Found {len(tiers)} tiers")
        
        app_config = {
            'app_name': app_name,
            'tiers': []
        }
        
        for tier_idx, tier in enumerate(tiers, 1):
            tier_name = tier.get('name')
            logger.info(f"\n[Tier {tier_idx}/{len(tiers)}] {tier_name}")
            logger.info("-" * 80)
            
            # Get nodes with availability check
            result = fetcher.get_active_nodes_with_availability(
                app_name=app_name,
                tier_name=tier_name,
                min_availability=args.min_availability,
                duration_mins=args.check_duration
            )
            
            total_nodes = result['total_nodes']
            active_nodes = result['active_nodes']
            inactive_nodes = result['inactive_nodes']
            node_availability = result['node_availability']
            
            stats['total_nodes_discovered'] += total_nodes
            stats['total_nodes_active'] += len(active_nodes)
            stats['total_nodes_inactive'] += len(inactive_nodes)
            
            if total_nodes == 0:
                logger.info("  No nodes found")
                continue
            
            logger.info(f"Total nodes: {total_nodes}")
            logger.info(f"Active nodes (≥{args.min_availability}%): {len(active_nodes)}")
            logger.info(f"Inactive nodes (<{args.min_availability}%): {len(inactive_nodes)}")
            
            # Show availability details if requested
            if args.show_availability:
                logger.info("\nNode Availability Details:")
                
                # Sort by availability (descending)
                sorted_nodes = sorted(
                    node_availability.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                for node_name, availability in sorted_nodes:
                    status = "✓ ACTIVE  " if availability >= args.min_availability else "✗ INACTIVE"
                    logger.info(f"  {status} {node_name}: {availability:.1f}%")
            else:
                # Just show active nodes
                if active_nodes:
                    logger.info("\nActive nodes:")
                    for node_name in active_nodes[:10]:  # Show first 10
                        availability = node_availability.get(node_name, 0)
                        logger.info(f"  ✓ {node_name} ({availability:.1f}%)")
                    
                    if len(active_nodes) > 10:
                        logger.info(f"  ... and {len(active_nodes) - 10} more")
            
            # Add to config if has active nodes
            if active_nodes:
                app_config['tiers'].append({
                    'tier_name': tier_name,
                    'nodes': active_nodes
                })
                stats['total_tiers'] += 1
                stats['tiers_with_active_nodes'] += 1
            else:
                logger.warning(f"  ⚠ No active nodes - tier excluded from config")
        
        # Add app to config if it has tiers with active nodes
        if app_config['tiers']:
            config['applications'].append(app_config)
            stats['apps_processed'] += 1
        else:
            logger.warning(f"\n⚠ Application '{app_name}' has no active nodes - excluded from config")
    
    # Save configuration
    logger.info("\n" + "=" * 80)
    logger.info("SAVING CONFIGURATION")
    logger.info("=" * 80)
    
    try:
        with open(args.output, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✓ Configuration saved to: {args.output}")
        
    except Exception as e:
        logger.error(f"✗ Error saving configuration: {e}")
        return 1
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("GENERATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Applications processed: {stats['apps_processed']}/{len(app_names)}")
    logger.info(f"Tiers with active nodes: {stats['tiers_with_active_nodes']}")
    logger.info(f"Total tiers in config: {stats['total_tiers']}")
    logger.info("")
    logger.info(f"Nodes discovered: {stats['total_nodes_discovered']}")
    logger.info(f"  ✓ Active (included): {stats['total_nodes_active']}")
    logger.info(f"  ✗ Inactive (filtered): {stats['total_nodes_inactive']}")
    
    if stats['total_nodes_discovered'] > 0:
        active_pct = (stats['total_nodes_active'] / stats['total_nodes_discovered']) * 100
        logger.info(f"\nActive percentage: {active_pct:.1f}%")
        logger.info(f"Reduction: {stats['total_nodes_inactive']} nodes filtered out")
    
    logger.info("=" * 80)
    
    # Show configuration preview
    logger.info("\nCONFIGURATION PREVIEW")
    logger.info("-" * 80)
    for app in config['applications']:
        logger.info(f"\nApplication: {app['app_name']}")
        for tier in app['tiers']:
            logger.info(f"  Tier: {tier['tier_name']}")
            logger.info(f"    Nodes: {len(tier['nodes'])}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())