#!/usr/bin/env python3
"""
Generate AppDynamics configuration file from application names
"""
import argparse
import json
import sys
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
                       help='Comma-separated list of application names (e.g., "App1,App2,App3")')
    
    # Output
    parser.add_argument('--output', required=True, 
                       help='Output JSON configuration file path')
    
    # Options
    parser.add_argument('--verify', action='store_true',
                       help='Verify configuration by testing a sample metric')
    parser.add_argument('--exclude-tiers', 
                       help='Comma-separated list of tier names to exclude')
    parser.add_argument('--exclude-nodes',
                       help='Comma-separated list of node names to exclude')
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger('ConfigGenerator')
    
    logger.info("=" * 80)
    logger.info("AppDynamics Configuration Generator")
    logger.info("=" * 80)
    
    # Parse application names
    app_names = [name.strip() for name in args.app_names.split(',')]
    logger.info(f"Applications to process: {len(app_names)}")
    for app in app_names:
        logger.info(f"  - {app}")
    
    # Parse exclusions
    exclude_tiers = []
    if args.exclude_tiers:
        exclude_tiers = [name.strip() for name in args.exclude_tiers.split(',')]
        logger.info(f"\nExcluding tiers: {', '.join(exclude_tiers)}")
    
    exclude_nodes = []
    if args.exclude_nodes:
        exclude_nodes = [name.strip() for name in args.exclude_nodes.split(',')]
        logger.info(f"Excluding nodes: {', '.join(exclude_nodes)}")
    
    # Initialize fetcher
    logger.info("\n→ Connecting to AppDynamics...")
    fetcher = AppDynamicsDataFetcher(
        controller_url=args.controller,
        account_name=args.account,
        username=args.username,
        password=args.password
    )
    
    # Test connection
    if not fetcher.test_connection():
        logger.error("✗ Connection failed!")
        return 1
    
    # Get all available applications to validate
    logger.info("\n→ Fetching available applications...")
    all_apps = fetcher.get_applications()
    
    if not all_apps:
        logger.error("✗ Could not fetch applications!")
        return 1
    
    available_app_names = [app.get('name') for app in all_apps]
    logger.info(f"✓ Found {len(available_app_names)} total applications in AppDynamics")
    
    # Validate requested apps exist
    invalid_apps = []
    for app_name in app_names:
        if app_name not in available_app_names:
            invalid_apps.append(app_name)
    
    if invalid_apps:
        logger.error(f"\n✗ Invalid application names: {', '.join(invalid_apps)}")
        logger.error(f"Available applications: {', '.join(available_app_names)}")
        return 1
    
    # Generate configuration
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING CONFIGURATION")
    logger.info("=" * 80)
    
    config = {
        'description': f'Auto-generated configuration for {len(app_names)} application(s)',
        'generated_at': str(datetime.now()),
        'applications': []
    }
    
    total_tiers = 0
    total_nodes = 0
    
    for app_idx, app_name in enumerate(app_names, 1):
        logger.info(f"\n[{app_idx}/{len(app_names)}] Processing: {app_name}")
        logger.info("-" * 80)
        
        # Get tiers for application
        tiers = fetcher.get_tiers_for_application(app_name)
        
        if not tiers:
            logger.warning(f"  ⚠ No tiers found for {app_name}")
            continue
        
        logger.info(f"  Found {len(tiers)} tiers")
        
        app_config = {
            'app_name': app_name,
            'tiers': []
        }
        
        for tier_idx, tier in enumerate(tiers, 1):
            tier_name = tier.get('name')
            
            # Check if tier should be excluded
            if tier_name in exclude_tiers:
                logger.info(f"  [{tier_idx}/{len(tiers)}] {tier_name} - EXCLUDED")
                continue
            
            logger.info(f"  [{tier_idx}/{len(tiers)}] {tier_name}")
            
            # Get nodes for tier
            nodes = fetcher.get_nodes_for_tier(app_name, tier_name)
            
            if not nodes:
                logger.info(f"      No nodes found (tier-level metrics only)")
                app_config['tiers'].append({
                    'tier_name': tier_name,
                    'nodes': []
                })
                total_tiers += 1
                continue
            
            # Filter nodes
            node_names = []
            for node in nodes:
                node_name = node.get('name')
                
                if node_name in exclude_nodes:
                    logger.info(f"      - {node_name} - EXCLUDED")
                    continue
                
                node_names.append(node_name)
                logger.info(f"      - {node_name}")
            
            if node_names:
                app_config['tiers'].append({
                    'tier_name': tier_name,
                    'nodes': node_names
                })
                total_tiers += 1
                total_nodes += len(node_names)
        
        if app_config['tiers']:
            config['applications'].append(app_config)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("CONFIGURATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Applications: {len(config['applications'])}")
    logger.info(f"Total Tiers: {total_tiers}")
    logger.info(f"Total Nodes: {total_nodes}")
    
    # Verify configuration if requested
    if args.verify and total_nodes > 0:
        logger.info("\n" + "=" * 80)
        logger.info("VERIFYING CONFIGURATION")
        logger.info("=" * 80)
        
        # Pick first app/tier/node to test
        test_app = config['applications'][0]
        test_tier = test_app['tiers'][0]
        test_node = test_tier['nodes'][0] if test_tier['nodes'] else None
        
        app_name = test_app['app_name']
        tier_name = test_tier['tier_name']
        
        logger.info(f"\n→ Testing sample metrics collection...")
        logger.info(f"  App: {app_name}")
        logger.info(f"  Tier: {tier_name}")
        
        if test_node:
            logger.info(f"  Node: {test_node}")
            
            # Test JVM metric
            test_path = f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{test_node}|JVM|Process CPU Usage %"
            logger.info(f"\n  Testing: {test_path}")
            
            data = fetcher.get_metric_data(app_name, test_path, duration_mins=15)
            
            if data:
                logger.info(f"  ✓ Success! Got {len(data)} data points")
                logger.info(f"    Latest value: {data[-1].get('value')}")
            else:
                logger.warning(f"  ⚠ No data (might need longer duration)")
        
        # Test tier-level metric
        test_path = f"Overall Application Performance|{tier_name}|Calls per Minute"
        logger.info(f"\n  Testing: {test_path}")
        
        data = fetcher.get_metric_data(app_name, test_path, duration_mins=15)
        
        if data:
            logger.info(f"  ✓ Success! Got {len(data)} data points")
            logger.info(f"    Latest value: {data[-1].get('value')}")
        else:
            logger.warning(f"  ⚠ No data (might need longer duration)")
    
    # Save configuration
    logger.info("\n→ Saving configuration...")
    
    try:
        with open(args.output, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✓ Configuration saved to: {args.output}")
        
        # Display file contents preview
        logger.info("\n" + "=" * 80)
        logger.info("CONFIGURATION FILE PREVIEW")
        logger.info("=" * 80)
        
        preview = json.dumps(config, indent=2)
        lines = preview.split('\n')
        
        if len(lines) > 50:
            logger.info('\n'.join(lines[:25]))
            logger.info(f"\n... ({len(lines) - 50} lines omitted) ...\n")
            logger.info('\n'.join(lines[-25:]))
        else:
            logger.info(preview)
        
    except Exception as e:
        logger.error(f"✗ Error saving configuration: {e}")
        return 1
    
    # Final instructions
    logger.info("\n" + "=" * 80)
    logger.info("✓ CONFIGURATION GENERATED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"\nTo use this configuration with monitoring:")
    logger.info(f"\npython3 monitoring_main.py \\")
    logger.info(f"    --run-id \"TEST_001\" \\")
    logger.info(f"    --duration 60 \\")
    logger.info(f"    --appd-controller \"{args.controller}\" \\")
    logger.info(f"    --appd-account \"{args.account}\" \\")
    logger.info(f"    --appd-user \"{args.username}\" \\")
    logger.info(f"    --appd-pass \"YOUR_PASSWORD\" \\")
    logger.info(f"    --appd-config \"{args.output}\" \\")
    logger.info(f"    --db-user \"oracle_user\" \\")
    logger.info(f"    --db-pass \"oracle_pass\" \\")
    logger.info(f"    --db-dsn \"host:1521/ORCL\"")
    
    return 0

if __name__ == '__main__':
    from datetime import datetime
    sys.exit(main())