#!/usr/bin/env python3
"""
Test script to discover and test AppDynamics metrics collection
Enhanced with metric path discovery
"""
import argparse
import json
from fetchers.appdynamics_fetcher import AppDynamicsDataFetcher
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(description='Test AppDynamics Metrics Collection')
    parser.add_argument('--controller', required=True, help='Controller URL')
    parser.add_argument('--account', required=True, help='Account name')
    parser.add_argument('--username', required=True, help='Username')
    parser.add_argument('--password', required=True, help='Password')
    
    # Single app/tier/node test mode
    parser.add_argument('--app-name', help='Application name to test')
    parser.add_argument('--tier-name', help='Tier name to test')
    parser.add_argument('--node-name', help='Node name to test')
    
    # Discovery mode
    parser.add_argument('--discover-all', action='store_true', 
                       help='Discover all apps/tiers/nodes')
    parser.add_argument('--discover-app', help='Discover tiers/nodes for specific app')
    parser.add_argument('--discover-tier', help='Discover nodes for specific tier (requires --app-name)')
    parser.add_argument('--discover-metrics', action='store_true',
                       help='Discover available metric paths (requires --app-name)')
    
    # Output
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--test-metrics', action='store_true', 
                       help='Test actual metrics collection')
    parser.add_argument('--duration', type=int, default=15,
                       help='Duration in minutes for metric collection (default: 15)')
    
    args = parser.parse_args()
    
    logger = setup_logger('AppDTest')
    
    # Initialize fetcher
    logger.info("Initializing AppDynamics connection...")
    fetcher = AppDynamicsDataFetcher(
        controller_url=args.controller,
        account_name=args.account,
        username=args.username,
        password=args.password
    )
    
    # Test connection
    if not fetcher.test_connection():
        logger.error("✗ Connection test failed!")
        return 1
    
    # Mode 1: Discover available metrics
    if args.discover_metrics and args.app_name:
        return discover_available_metrics(fetcher, args.app_name, args.tier_name, 
                                         args.node_name, logger)
    
    # Mode 2: Test single app/tier/node
    elif args.app_name and args.tier_name and args.node_name:
        return test_single_config(fetcher, args, logger)
    
    # Mode 3: Discover specific tier's nodes
    elif args.discover_tier and args.app_name:
        return discover_tier_nodes(fetcher, args.app_name, args.discover_tier, logger)
    
    # Mode 4: Discover specific app's tiers and nodes
    elif args.discover_app:
        return discover_app_tiers(fetcher, args.discover_app, args.output, logger)
    
    # Mode 5: Discover all applications
    elif args.discover_all:
        return discover_all_apps(fetcher, args.output, logger)
    
    else:
        logger.error("Please specify one of the following modes:")
        logger.error("  1. Test single: --app-name --tier-name --node-name [--test-metrics]")
        logger.error("  2. Discover metrics: --discover-metrics --app-name [--tier-name] [--node-name]")
        logger.error("  3. Discover tier: --discover-tier <tier> --app-name <app>")
        logger.error("  4. Discover app: --discover-app <app>")
        logger.error("  5. Discover all: --discover-all")
        return 1

def discover_available_metrics(fetcher, app_name, tier_name=None, node_name=None, logger=None):
    """Discover what metrics are actually available"""
    
    logger.info("\n" + "=" * 80)
    logger.info("DISCOVERING AVAILABLE METRICS")
    logger.info("=" * 80)
    logger.info(f"Application: {app_name}")
    if tier_name:
        logger.info(f"Tier: {tier_name}")
    if node_name:
        logger.info(f"Node: {node_name}")
    logger.info("=" * 80)
    
    # Discover metrics at different levels
    metric_browser_paths = []
    
    # Root level
    if tier_name and node_name:
        # Node level metrics
        metric_browser_paths = [
            f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}",
            f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}|JVM",
            f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}|Hardware Resources",
        ]
    elif tier_name:
        # Tier level metrics
        metric_browser_paths = [
            f"Overall Application Performance|{tier_name}",
            f"Application Infrastructure Performance|{tier_name}",
        ]
    else:
        # Application level
        metric_browser_paths = [
            "Overall Application Performance",
            "Application Infrastructure Performance",
        ]
    
    all_discovered = {}
    
    for base_path in metric_browser_paths:
        logger.info(f"\n→ Exploring: {base_path}")
        
        discovered = discover_metrics_recursive(fetcher, app_name, base_path, logger, depth=0, max_depth=3)
        if discovered:
            all_discovered[base_path] = discovered
            logger.info(f"  ✓ Found {len(discovered)} metric paths")
    
    # Display summary
    logger.info("\n" + "=" * 80)
    logger.info("DISCOVERED METRIC PATHS")
    logger.info("=" * 80)
    
    total_metrics = 0
    for base_path, metrics in all_discovered.items():
        logger.info(f"\n{base_path}:")
        for metric_path in metrics[:10]:  # Show first 10
            logger.info(f"  - {metric_path}")
        if len(metrics) > 10:
            logger.info(f"  ... and {len(metrics) - 10} more")
        total_metrics += len(metrics)
    
    logger.info(f"\n✓ Total discovered metrics: {total_metrics}")
    
    return 0

def discover_metrics_recursive(fetcher, app_name, metric_path, logger, depth=0, max_depth=3):
    """Recursively discover available metrics"""
    
    if depth > max_depth:
        return []
    
    url = f"{fetcher.controller_url}/controller/rest/applications/{app_name}/metrics"
    
    params = {
        'metric-path': metric_path,
        'output': 'JSON'
    }
    
    try:
        response = fetcher.session.get(url, params=params, verify=False, timeout=30)
        response.raise_for_status()
        
        metrics = response.json()
        discovered = []
        
        for metric in metrics:
            metric_name = metric.get('name', '')
            metric_type = metric.get('type', '')
            
            full_path = f"{metric_path}|{metric_name}"
            
            if metric_type == 'leaf':
                # This is an actual metric
                discovered.append(full_path)
            elif metric_type == 'folder' and depth < max_depth:
                # Recurse into folder
                sub_metrics = discover_metrics_recursive(
                    fetcher, app_name, full_path, logger, depth + 1, max_depth
                )
                discovered.extend(sub_metrics)
        
        return discovered
        
    except Exception as e:
        logger.debug(f"Error discovering metrics at {metric_path}: {e}")
        return []

def test_single_config(fetcher, args, logger):
    """Test metrics collection for single app/tier/node"""
    
    app_name = args.app_name
    tier_name = args.tier_name
    node_name = args.node_name
    duration = args.duration
    
    logger.info("\n" + "=" * 80)
    logger.info("TESTING SINGLE CONFIGURATION")
    logger.info("=" * 80)
    logger.info(f"Application: {app_name}")
    logger.info(f"Tier: {tier_name}")
    logger.info(f"Node: {node_name}")
    logger.info(f"Duration: {duration} minutes")
    logger.info("=" * 80)
    
    # Verify application exists
    logger.info("\n→ Verifying application exists...")
    apps = fetcher.get_applications()
    if apps:
        app_names = [app.get('name') for app in apps]
        if app_name in app_names:
            logger.info(f"  ✓ Application '{app_name}' found")
        else:
            logger.error(f"  ✗ Application '{app_name}' not found")
            logger.info(f"  Available applications: {', '.join(app_names)}")
            return 1
    
    # Verify tier exists
    logger.info("\n→ Verifying tier exists...")
    tiers = fetcher.get_tiers_for_application(app_name)
    if tiers:
        tier_names = [tier.get('name') for tier in tiers]
        if tier_name in tier_names:
            logger.info(f"  ✓ Tier '{tier_name}' found")
        else:
            logger.error(f"  ✗ Tier '{tier_name}' not found")
            logger.info(f"  Available tiers: {', '.join(tier_names)}")
            return 1
    
    # Verify node exists
    logger.info("\n→ Verifying node exists...")
    nodes = fetcher.get_nodes_for_tier(app_name, tier_name)
    if nodes:
        node_names = [node.get('name') for node in nodes]
        if node_name in node_names:
            logger.info(f"  ✓ Node '{node_name}' found")
        else:
            logger.error(f"  ✗ Node '{node_name}' not found")
            logger.info(f"  Available nodes: {', '.join(node_names)}")
            return 1
    
    # Test metrics collection if requested
    if args.test_metrics:
        logger.info("\n" + "=" * 80)
        logger.info("TESTING METRICS COLLECTION")
        logger.info("=" * 80)
        
        # First, try to discover what metrics are actually available
        logger.info("\n→ Discovering available metrics first...")
        
        # Test a simple metric path to see if we can get any data
        test_paths = [
            f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}|Agent|Availability",
            f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}|JVM|Process CPU Usage %",
            f"Overall Application Performance|{tier_name}|Calls per Minute",
        ]
        
        logger.info("\n→ Testing sample metric paths...")
        for test_path in test_paths:
            logger.info(f"\n  Testing: {test_path}")
            data = fetcher.get_metric_data(app_name, test_path, duration_mins=duration)
            if data:
                logger.info(f"    ✓ Success! Got {len(data)} data points")
                logger.info(f"    Sample: {data[0]}")
            else:
                logger.warning(f"    ⚠ No data returned")
        
        # Test Server Metrics
        logger.info("\n→ Testing Server Metrics...")
        server_metrics = fetcher.get_server_metrics(app_name, tier_name, node_name, duration_mins=duration)
        
        total_server_points = 0
        successful_server_metrics = []
        failed_server_metrics = []
        
        for metric_name, values in server_metrics.items():
            if values:
                total_server_points += len(values)
                successful_server_metrics.append(metric_name)
                logger.info(f"  ✓ {metric_name}: {len(values)} data points")
                if values:
                    latest = values[-1]
                    logger.info(f"      Latest: {latest.get('value')} at {latest.get('timestamp')}")
            else:
                failed_server_metrics.append(metric_name)
        
        if failed_server_metrics:
            logger.warning(f"\n  ⚠ No data for these server metrics:")
            for metric_name in failed_server_metrics:
                logger.warning(f"    - {metric_name}")
        
        logger.info(f"\n  Server Metrics Summary: {len(successful_server_metrics)}/{len(server_metrics)} successful, {total_server_points} total data points")
        
        # Test JVM Metrics
        logger.info("\n→ Testing JVM Metrics...")
        jvm_metrics = fetcher.get_jvm_metrics(app_name, tier_name, node_name, duration_mins=duration)
        
        total_jvm_points = 0
        successful_jvm_metrics = []
        failed_jvm_metrics = []
        
        for metric_name, values in jvm_metrics.items():
            if values:
                total_jvm_points += len(values)
                successful_jvm_metrics.append(metric_name)
                logger.info(f"  ✓ {metric_name}: {len(values)} data points")
                if values:
                    latest = values[-1]
                    logger.info(f"      Latest: {latest.get('value')} at {latest.get('timestamp')}")
            else:
                failed_jvm_metrics.append(metric_name)
        
        if failed_jvm_metrics:
            logger.warning(f"\n  ⚠ No data for these JVM metrics:")
            for metric_name in failed_jvm_metrics:
                logger.warning(f"    - {metric_name}")
        
        logger.info(f"\n  JVM Metrics Summary: {len(successful_jvm_metrics)}/{len(jvm_metrics)} successful, {total_jvm_points} total data points")
        
        # Test Application Metrics
        logger.info("\n→ Testing Application Metrics...")
        app_metrics = fetcher.get_application_metrics(app_name, tier_name, duration_mins=duration)
        
        total_app_points = 0
        successful_app_metrics = []
        failed_app_metrics = []
        
        for metric_name, values in app_metrics.items():
            if values:
                total_app_points += len(values)
                successful_app_metrics.append(metric_name)
                logger.info(f"  ✓ {metric_name}: {len(values)} data points")
                if values:
                    latest = values[-1]
                    logger.info(f"      Latest: {latest.get('value')} at {latest.get('timestamp')}")
            else:
                failed_app_metrics.append(metric_name)
        
        if failed_app_metrics:
            logger.warning(f"\n  ⚠ No data for these application metrics:")
            for metric_name in failed_app_metrics:
                logger.warning(f"    - {metric_name}")
        
        logger.info(f"\n  Application Metrics Summary: {len(successful_app_metrics)}/{len(app_metrics)} successful, {total_app_points} total data points")
        
        # Overall Summary
        logger.info("\n" + "=" * 80)
        logger.info("METRICS COLLECTION SUMMARY")
        logger.info("=" * 80)
        total_all = total_server_points + total_jvm_points + total_app_points
        logger.info(f"Total Data Points Collected: {total_all}")
        logger.info(f"  - Server Metrics: {total_server_points} ({len(successful_server_metrics)}/{len(server_metrics)} metrics)")
        logger.info(f"  - JVM Metrics: {total_jvm_points} ({len(successful_jvm_metrics)}/{len(jvm_metrics)} metrics)")
        logger.info(f"  - Application Metrics: {total_app_points} ({len(successful_app_metrics)}/{len(app_metrics)} metrics)")
        
        if total_all == 0:
            logger.error("\n✗ NO DATA COLLECTED!")
            logger.error("\nPossible reasons:")
            logger.error("  1. The node/tier may not be actively reporting metrics")
            logger.error("  2. The metric paths may not match your AppDynamics version")
            logger.error("  3. The time range may have no data")
            logger.error("\nTroubleshooting steps:")
            logger.error("  1. Verify the node is active in AppDynamics UI")
            logger.error("  2. Try increasing --duration (e.g., --duration 60)")
            logger.error("  3. Run with --discover-metrics to see available metric paths")
            return 1
    
    # Generate configuration file
    if args.output:
        config = {
            'description': 'Test Configuration',
            'applications': [
                {
                    'app_name': app_name,
                    'tiers': [
                        {
                            'tier_name': tier_name,
                            'nodes': [node_name]
                        }
                    ]
                }
            ]
        }
        
        with open(args.output, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"\n✓ Configuration saved to: {args.output}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✓ TEST COMPLETED")
    logger.info("=" * 80)
    
    return 0

def discover_tier_nodes(fetcher, app_name, tier_name, logger):
    """Discover nodes for a specific tier"""
    
    logger.info("\n" + "=" * 80)
    logger.info(f"DISCOVERING NODES FOR TIER")
    logger.info("=" * 80)
    logger.info(f"Application: {app_name}")
    logger.info(f"Tier: {tier_name}")
    logger.info("=" * 80)
    
    nodes = fetcher.get_nodes_for_tier(app_name, tier_name)
    
    if not nodes:
        logger.warning(f"No nodes found for tier '{tier_name}'")
        return 1
    
    logger.info(f"\nFound {len(nodes)} nodes:")
    for idx, node in enumerate(nodes, 1):
        node_name = node.get('name')
        node_type = node.get('type', 'Unknown')
        machine_name = node.get('machineName', 'Unknown')
        agent_type = node.get('agentType', 'Unknown')
        
        logger.info(f"\n[{idx}] {node_name}")
        logger.info(f"    Type: {node_type}")
        logger.info(f"    Machine: {machine_name}")
        logger.info(f"    Agent: {agent_type}")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"Total Nodes: {len(nodes)}")
    logger.info("=" * 80)
    
    return 0

def discover_app_tiers(fetcher, app_name, output_file, logger):
    """Discover tiers and nodes for a specific application"""
    
    logger.info("\n" + "=" * 80)
    logger.info(f"DISCOVERING APPLICATION: {app_name}")
    logger.info("=" * 80)
    
    # Get tiers
    tiers = fetcher.get_tiers_for_application(app_name)
    if not tiers:
        logger.error(f"No tiers found for application '{app_name}'")
        return 1
    
    logger.info(f"\nFound {len(tiers)} tiers:")
    
    app_config = {
        'app_name': app_name,
        'tiers': []
    }
    
    for tier_idx, tier in enumerate(tiers, 1):
        tier_name = tier.get('name')
        tier_type = tier.get('type', 'Unknown')
        
        logger.info(f"\n[Tier {tier_idx}] {tier_name} ({tier_type})")
        
        # Get nodes for tier
        nodes = fetcher.get_nodes_for_tier(app_name, tier_name)
        node_names = []
        
        if nodes:
            logger.info(f"  Nodes: {len(nodes)}")
            for node in nodes:
                node_name = node.get('name')
                node_names.append(node_name)
                logger.info(f"    - {node_name}")
        else:
            logger.info(f"  No nodes found")
        
        app_config['tiers'].append({
            'tier_name': tier_name,
            'nodes': node_names
        })
    
    # Save configuration
    if output_file:
        config = {
            'description': f'Auto-discovered configuration for {app_name}',
            'applications': [app_config]
        }
        
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"\n✓ Configuration saved to: {output_file}")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"Total Tiers: {len(tiers)}")
    total_nodes = sum(len(t['nodes']) for t in app_config['tiers'])
    logger.info(f"Total Nodes: {total_nodes}")
    logger.info("=" * 80)
    
    return 0

def discover_all_apps(fetcher, output_file, logger):
    """Discover all applications with their tiers and nodes"""
    
    logger.info("\n" + "=" * 80)
    logger.info("DISCOVERING ALL APPLICATIONS")
    logger.info("=" * 80)
    
    # Get all applications
    apps = fetcher.get_applications()
    if not apps:
        logger.error("No applications found!")
        return 1
    
    logger.info(f"\nFound {len(apps)} applications")
    
    config = {
        'description': 'Auto-discovered AppDynamics Configuration',
        'applications': []
    }
    
    for app_idx, app in enumerate(apps, 1):
        app_name = app.get('name')
        logger.info(f"\n{'=' * 80}")
        logger.info(f"[Application {app_idx}/{len(apps)}] {app_name}")
        logger.info(f"{'=' * 80}")
        
        # Get tiers
        tiers = fetcher.get_tiers_for_application(app_name)
        if not tiers:
            logger.warning(f"  No tiers found")
            continue
        
        app_config = {
            'app_name': app_name,
            'tiers': []
        }
        
        for tier_idx, tier in enumerate(tiers, 1):
            tier_name = tier.get('name')
            logger.info(f"\n  [Tier {tier_idx}/{len(tiers)}] {tier_name}")
            
            # Get nodes
            nodes = fetcher.get_nodes_for_tier(app_name, tier_name)
            node_names = []
            
            if nodes:
                node_names = [node.get('name') for node in nodes]
                logger.info(f"    Nodes: {len(node_names)}")
                for node_name in node_names:
                    logger.info(f"      - {node_name}")
            else:
                logger.info(f"    No nodes found")
            
            app_config['tiers'].append({
                'tier_name': tier_name,
                'nodes': node_names
            })
        
        config['applications'].append(app_config)
    
    # Save configuration
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"\n✓ Configuration saved to: {output_file}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("DISCOVERY SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Applications: {len(config['applications'])}")
    total_tiers = sum(len(app['tiers']) for app in config['applications'])
    logger.info(f"Total Tiers: {total_tiers}")
    total_nodes = sum(
        len(tier['nodes']) 
        for app in config['applications'] 
        for tier in app['tiers']
    )
    logger.info(f"Total Nodes: {total_nodes}")
    logger.info("=" * 80)
    
    return 0

if __name__ == '__main__':
    exit(main())