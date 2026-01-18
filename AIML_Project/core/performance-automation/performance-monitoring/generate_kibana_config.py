#!/usr/bin/env python3
"""
Generate Kibana configuration file from visualization IDs or dashboard ID
"""
import argparse
import json
import sys
from fetchers.kibana_fetcher import KibanaDataFetcher
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(
        description='Generate Kibana configuration from visualization/dashboard IDs'
    )
    
    # Kibana credentials
    parser.add_argument('--kibana-url', required=True, help='Kibana URL')
    parser.add_argument('--kibana-user', required=True, help='Kibana username')
    parser.add_argument('--kibana-pass', required=True, help='Kibana password')
    
    # Input options
    parser.add_argument('--viz-ids', 
                       help='Comma-separated list of visualization IDs')
    parser.add_argument('--dashboard-id',
                       help='Dashboard ID (will extract all visualizations from dashboard)')
    parser.add_argument('--auto-discover', action='store_true',
                       help='Auto-discover all visualizations')
    
    # Output
    parser.add_argument('--output', required=True,
                       help='Output JSON configuration file path')
    
    args = parser.parse_args()
    
    logger = setup_logger('KibanaConfigGen')
    
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
    
    visualizations = []
    
    # Mode 1: Specific visualization IDs
    if args.viz_ids:
        viz_ids = [vid.strip() for vid in args.viz_ids.split(',')]
        logger.info(f"\n→ Processing {len(viz_ids)} visualization IDs...")
        
        for viz_id in viz_ids:
            viz_data = fetcher.get_visualization_data(viz_id)
            if viz_data:
                title = viz_data.get('attributes', {}).get('title', viz_id)
                visualizations.append({
                    'id': viz_id,
                    'name': title
                })
                logger.info(f"  ✓ {title} ({viz_id})")
            else:
                logger.warning(f"  ⚠ Could not fetch: {viz_id}")
    
    # Mode 2: Extract from dashboard
    elif args.dashboard_id:
        logger.info(f"\n→ Extracting visualizations from dashboard: {args.dashboard_id}")
        
        dash_data = fetcher.get_dashboard_data(args.dashboard_id)
        if dash_data:
            attributes = dash_data.get('attributes', {})
            panels_json = attributes.get('panelsJSON', '[]')
            
            try:
                panels = json.loads(panels_json)
                logger.info(f"  Found {len(panels)} panels")
                
                for panel in panels:
                    if 'id' in panel:
                        viz_id = panel['id']
                        viz_data = fetcher.get_visualization_data(viz_id)
                        if viz_data:
                            title = viz_data.get('attributes', {}).get('title', viz_id)
                            visualizations.append({
                                'id': viz_id,
                                'name': title
                            })
                            logger.info(f"  ✓ {title} ({viz_id})")
            except Exception as e:
                logger.error(f"  ✗ Error parsing dashboard: {e}")
                return 1
        else:
            logger.error("  ✗ Could not fetch dashboard")
            return 1
    
    # Mode 3: Auto-discover
    elif args.auto_discover:
        logger.info("\n→ Auto-discovering all visualizations...")
        
        url = f"{fetcher.kibana_url}/api/saved_objects/_find"
        params = {'type': 'visualization', 'per_page': 100}
        
        try:
            response = fetcher.session.get(url, params=params, verify=False, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            saved_objects = data.get('saved_objects', [])
            
            logger.info(f"  Found {len(saved_objects)} visualizations")
            
            for obj in saved_objects:
                viz_id = obj.get('id')
                title = obj.get('attributes', {}).get('title', viz_id)
                visualizations.append({
                    'id': viz_id,
                    'name': title
                })
                logger.info(f"  ✓ {title} ({viz_id})")
        except Exception as e:
            logger.error(f"  ✗ Error discovering visualizations: {e}")
            return 1
    
    else:
        logger.error("Please specify --viz-ids, --dashboard-id, or --auto-discover")
        return 1
    
    # Generate configuration
    config = {
        'description': f'Kibana configuration with {len(visualizations)} visualizations',
        'generated_at': str(datetime.now()),
        'kibana_url': args.kibana_url,
        'visualizations': visualizations
    }
    
    # Save
    try:
        with open(args.output, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"\n✓ Configuration saved to: {args.output}")
        logger.info(f"\nTotal visualizations: {len(visualizations)}")
        
        # Show usage
        logger.info("\n" + "=" * 80)
        logger.info("To use with monitoring:")
        logger.info("=" * 80)
        
        viz_ids_str = ','.join([v['id'] for v in visualizations])
        logger.info(f"\npython3 monitoring_main.py \\")
        logger.info(f"    --kibana-viz-ids \"{viz_ids_str}\" \\")
        logger.info(f"    ... other parameters ...")
        
    except Exception as e:
        logger.error(f"✗ Error saving configuration: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    from datetime import datetime
    sys.exit(main())