#!/usr/bin/env python3
"""
Generate AppDynamics configuration - Filter by Active Metrics
Only includes nodes that have Calls per Minute data (App Agent Status = 100%)
"""
import argparse
import json
import sys
from datetime import datetime
from fetchers.appdynamics_fetcher import AppDynamicsDataFetcher
from utils.logger import setup_logger
import time

def main():
    parser = argparse.ArgumentParser(
        description='Generate AppDynamics config - Active nodes with metrics only'
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
    parser.add_argument('--check-duration', type=int, default=15,
                       help='Check for metrics in last N minutes (default: 15)')
    parser.add_argument('--require-calls', action='store_true', default=True,
                       help='Require node to have calls > 0 (default: True)')
    
    # Output
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--show-metrics', action='store_true',
                       help='Show calls/min for each node')
    parser.add_argument('--quick-check', action='store_true',
                       help='Use quick 5-minute check instead of 15 minutes')
    
    args = parser.parse_args()
    
    # Setup logger
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger('AppDConfigGenerator', level=log_level)
    
    check_duration = 5 if args.quick_check else args.check_duration
    
    logger.info("=" * 80)
    logger.info("AppDynamics Config Generator - Active Metrics Filter")
    logger.info("=" * 80)
    logger.info(f"Filter: Nodes with Calls per Minute data (App Agent Status = 100%)")
    logger.info(f"Check Period: {check_duration} minutes")
    logger.info("=" * 80)
    
    # Parse app names
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
        logger.error(f"Available: {', '.join(available_app_names)}")
        return 1
    
    # Generate configuration
    logger.info("\n" + "=" * 80)
    logger.info("DISCOVERING ACTIVE NODES")
    logger.info("=" * 80)
    
    config = {
        'description': 'AppDynamics config - Active nodes with metrics',
        'generated_at': datetime.now().isoformat(),
        'filter_criteria': {
            'method': 'Calls per Minute metric presence',
            'check_period_minutes': check_duration,
            'require_active_calls': args.require_calls
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
        'tiers_with_active_nodes': 0,
        'total_calls_per_min': 0.0
    }
    
    start_time = time.time()
    
    for app_idx, app_name in enumerate(app_names, 1):
        logger.info(f"\n{'=' * 80}")
        logger.info(f"[{app_idx}/{len(app_names)}] Processing: {app_name}")
        logger.info(f"{'=' * 80}")
        
        tiers = fetcher.get_tiers_for_application(app_name)
        if not tiers:
            logger.warning(f"No tiers found for {app_name}")
            continue
        
        logger.info(f"Found {len(tiers)} tiers\n")
        
        app_config = {
            'app_name': app_name,
            'tiers': []
        }
        
        for tier_idx, tier in enumerate(tiers, 1):
            tier_name = tier.get('name')
            logger.info(f"[Tier {tier_idx}/{len(tiers)}] {tier_name}")
            logger.info("-" * 80)
            
            # Get nodes with metric check
            logger.info("  Checking node metrics...")
            
            result = fetcher.get_active_nodes_by_metrics(
                app_name=app_name,
                tier_name=tier_name,
                require_calls=args.require_calls,
                duration_mins=check_duration
            )
            
            total_nodes = result['total_nodes']
            active_nodes = result['active_nodes']
            inactive_nodes = result['inactive_nodes']
            node_metrics = result['node_metrics']
            
            stats['total_nodes_discovered'] += total_nodes
            stats['total_nodes_active'] += len(active_nodes)
            stats['total_nodes_inactive'] += len(inactive_nodes)
            
            if total_nodes == 0:
                logger.info("  No nodes found\n")
                continue
            
            logger.info(f"  Total nodes: {total_nodes}")
            logger.info(f"  ✓ Active (with metrics): {len(active_nodes)}")
            logger.info(f"  ✗ Inactive (no metrics): {len(inactive_nodes)}")
            
            # Calculate tier statistics
            tier_total_calls = sum(
                m['calls_per_min'] for m in node_metrics.values()
            )
            stats['total_calls_per_min'] += tier_total_calls
            
            if tier_total_calls > 0:
                logger.info(f"  Total calls/min: {tier_total_calls:.2f}")
            
            # Show detailed metrics if requested
            if args.show_metrics and active_nodes:
                logger.info("\n  Active Node Metrics:")
                
                # Sort by calls per minute (descending)
                sorted_nodes = sorted(
                    [(name, node_metrics[name]) for name in active_nodes],
                    key=lambda x: x[1]['calls_per_min'],
                    reverse=True
                )
                
                for node_name, metrics in sorted_nodes[:10]:  # Show top 10
                    calls = metrics['calls_per_min']
                    data_points = metrics['data_points']
                    logger.info(f"    ✓ {node_name}: {calls:.2f} calls/min ({data_points} data points)")
                
                if len(sorted_nodes) > 10:
                    logger.info(f"    ... and {len(sorted_nodes) - 10} more active nodes")
            
            elif active_nodes and not args.show_metrics:
                logger.info(f"\n  Active nodes (showing first 5):")
                for node_name in active_nodes[:5]:
                    calls = node_metrics[node_name]['calls_per_min']
                    logger.info(f"    ✓ {node_name} ({calls:.2f} calls/min)")
                
                if len(active_nodes) > 5:
                    logger.info(f"    ... and {len(active_nodes) - 5} more")
            
            # Show sample inactive nodes if verbose
            if args.verbose and inactive_nodes:
                logger.info(f"\n  Sample inactive nodes (first 3):")
                for node_name in inactive_nodes[:3]:
                    logger.info(f"    ✗ {node_name} (no metrics)")
            
            logger.info("")  # Blank line
            
            # Add to config if has active nodes
            if active_nodes:
                app_config['tiers'].append({
                    'tier_name': tier_name,
                    'nodes': active_nodes,
                    'total_calls_per_min': tier_total_calls
                })
                stats['total_tiers'] += 1
                stats['tiers_with_active_nodes'] += 1
            else:
                logger.warning(f"  ⚠ No active nodes - tier excluded from config\n")
        
        # Add app to config if it has active tiers
        if app_config['tiers']:
            config['applications'].append(app_config)
            stats['apps_processed'] += 1
        else:
            logger.warning(f"\n⚠ Application '{app_name}' has no active nodes - excluded\n")
    
    elapsed_time = time.time() - start_time
    
    # Save configuration
    logger.info("=" * 80)
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
    logger.info(f"Applications in config: {stats['apps_processed']}/{len(app_names)}")
    logger.info(f"Tiers with active nodes: {stats['tiers_with_active_nodes']}")
    logger.info(f"Total tiers in config: {stats['total_tiers']}")
    logger.info("")
    logger.info(f"Total nodes discovered: {stats['total_nodes_discovered']}")
    logger.info(f"  ✓ Active (with metrics): {stats['total_nodes_active']}")
    logger.info(f"  ✗ Inactive (no metrics): {stats['total_nodes_inactive']}")
    
    if stats['total_nodes_discovered'] > 0:
        active_pct = (stats['total_nodes_active'] / stats['total_nodes_discovered']) * 100
        reduction = stats['total_nodes_inactive']
        
        logger.info(f"\nActive percentage: {active_pct:.1f}%")
        logger.info(f"Nodes filtered out: {reduction} ({100-active_pct:.1f}%)")
        logger.info(f"Total traffic: {stats['total_calls_per_min']:.2f} calls/min")
    
    logger.info(f"\nExecution time: {elapsed_time:.1f} seconds")
    logger.info("=" * 80)
    
    # Configuration preview
    if stats['apps_processed'] > 0:
        logger.info("\nCONFIGURATION PREVIEW")
        logger.info("-" * 80)
        for app in config['applications']:
            logger.info(f"\n✓ Application: {app['app_name']}")
            for tier in app['tiers']:
                node_count = len(tier['nodes'])
                calls = tier.get('total_calls_per_min', 0)
                logger.info(f"    Tier: {tier['tier_name']}")
                logger.info(f"      Nodes: {node_count}")
                logger.info(f"      Traffic: {calls:.2f} calls/min")
        logger.info("")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())