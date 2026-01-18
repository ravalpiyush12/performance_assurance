#!/usr/bin/env python3
"""
Generate Kibana configuration from all dashboards
"""
import argparse
import json
import sys
from datetime import datetime
from fetchers.kibana_fetcher import KibanaDataFetcher
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(
        description='Generate Kibana configuration from dashboards'
    )
    
    # Kibana credentials
    parser.add_argument('--kibana-url', required=True, help='Kibana URL')
    parser.add_argument('--kibana-user', required=True, help='Kibana username')
    parser.add_argument('--kibana-pass', required=True, help='Kibana password')
    
    # Dashboard selection
    parser.add_argument('--dashboard-ids', 
                       help='Comma-separated dashboard IDs (leave empty for all dashboards)')
    parser.add_argument('--dashboard-names',
                       help='Comma-separated dashboard names to filter')
    
    # Output
    parser.add_argument('--output', required=True,
                       help='Output JSON configuration file path')
    
    args = parser.parse_args()
    
    logger = setup_logger('KibanaConfigGenerator')
    
    logger.info("=" * 80)
    logger.info("Kibana Configuration Generator")
    logger.info("=" * 80)
    
    # Initialize fetcher
    logger.info("\n→ Connecting to Kibana...")
    fetcher = KibanaDataFetcher(
        kibana_url=args.kibana_url,
        username=args.kibana_user,
        password=args.kibana_pass
    )
    
    if not fetcher.test_connection():
        logger.error("✗ Connection failed!")
        return 1
    
    # Get dashboards
    logger.info("\n→ Fetching dashboards...")
    
    url = f"{fetcher.kibana_url}/api/saved_objects/_find"
    params = {'type': 'dashboard', 'per_page': 100}
    
    try:
        response = fetcher.session.get(url, params=params, verify=False, timeout=30)
        response.raise_for_status()
        data = response.json()
        all_dashboards = data.get('saved_objects', [])
        
        logger.info(f"✓ Found {len(all_dashboards)} total dashboards")
        
    except Exception as e:
        logger.error(f"✗ Error fetching dashboards: {e}")
        return 1
    
    # Filter dashboards
    selected_dashboards = []
    
    if args.dashboard_ids:
        # Specific IDs
        requested_ids = [did.strip() for did in args.dashboard_ids.split(',')]
        selected_dashboards = [d for d in all_dashboards if d.get('id') in requested_ids]
        logger.info(f"Selected {len(selected_dashboards)} dashboards by ID")
        
    elif args.dashboard_names:
        # Filter by name
        requested_names = [name.strip().lower() for name in args.dashboard_names.split(',')]
        selected_dashboards = [
            d for d in all_dashboards 
            if any(name in d.get('attributes', {}).get('title', '').lower() for name in requested_names)
        ]
        logger.info(f"Selected {len(selected_dashboards)} dashboards by name")
        
    else:
        # All dashboards
        selected_dashboards = all_dashboards
        logger.info(f"Selected all {len(selected_dashboards)} dashboards")
    
    if not selected_dashboards:
        logger.error("✗ No dashboards selected!")
        return 1
    
    # Generate configuration
    logger.info("\n" + "=" * 80)
    logger.info("PROCESSING DASHBOARDS")
    logger.info("=" * 80)
    
    config = {
        'description': 'Kibana monitoring configuration',
        'generated_at': datetime.now().isoformat(),
        'dashboards': []
    }
    
    for dash_idx, dashboard in enumerate(selected_dashboards, 1):
        dash_id = dashboard.get('id')
        dash_title = dashboard.get('attributes', {}).get('title', 'Unknown')
        
        logger.info(f"\n[{dash_idx}/{len(selected_dashboards)}] {dash_title}")
        logger.info(f"  ID: {dash_id}")
        
        # Get panels from dashboard
        panels_json = dashboard.get('attributes', {}).get('panelsJSON', '[]')
        try:
            panels = json.loads(panels_json)
            logger.info(f"  Panels: {len(panels)}")
            
            config['dashboards'].append({
                'id': dash_id,
                'name': dash_title,
                'panel_count': len(panels)
            })
            
        except Exception as e:
            logger.warning(f"  Error parsing panels: {e}")
            config['dashboards'].append({
                'id': dash_id,
                'name': dash_title,
                'panel_count': 0
            })
    
    # Save configuration
    logger.info("\n→ Saving configuration...")
    try:
        with open(args.output, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✓ Saved to: {args.output}")
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Dashboards: {len(config['dashboards'])}")
        total_panels = sum(d['panel_count'] for d in config['dashboards'])
        logger.info(f"Total Panels: {total_panels}")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ Error saving: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())