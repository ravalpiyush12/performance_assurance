#!/usr/bin/env python3
"""
Test script for Kibana data collection
"""
import argparse
import json
import sys
from datetime import datetime
from fetchers.kibana_fetcher import KibanaDataFetcher
from utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(description='Test Kibana Data Collection')
    
    # Kibana credentials
    parser.add_argument('--kibana-url', required=True, help='Kibana URL')
    parser.add_argument('--kibana-user', required=True, help='Kibana username')
    parser.add_argument('--kibana-pass', required=True, help='Kibana password')
    
    # Test modes
    parser.add_argument('--test-connection', action='store_true',
                       help='Test basic connection to Kibana')
    parser.add_argument('--list-index-patterns', action='store_true',
                       help='List all available index patterns')
    parser.add_argument('--list-dashboards', action='store_true',
                       help='List all dashboards')
    
    # Specific tests
    parser.add_argument('--test-dashboard', help='Test fetching specific dashboard by ID')
    parser.add_argument('--test-index-search', help='Test searching specific index pattern')
    
    # Output
    parser.add_argument('--output', help='Output JSON file for discovered items')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logger
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger('KibanaTest', level=log_level)
    
    logger.info("=" * 80)
    logger.info("Kibana Test Utility")
    logger.info("=" * 80)
    logger.info(f"Kibana URL: {args.kibana_url}")
    logger.info("=" * 80)
    
    # Initialize fetcher
    logger.info("\n→ Initializing Kibana connection...")
    fetcher = KibanaDataFetcher(
        kibana_url=args.kibana_url,
        username=args.kibana_user,
        password=args.kibana_pass
    )
    
    # Test connection
    if args.test_connection or not any([
        args.list_index_patterns,
        args.list_dashboards,
        args.test_dashboard,
        args.test_index_search
    ]):
        test_connection(fetcher, logger)
        if args.test_connection:
            return 0
    
    # List index patterns
    if args.list_index_patterns:
        list_index_patterns(fetcher, logger, args.output)
    
    # List dashboards
    if args.list_dashboards:
        list_dashboards(fetcher, logger, args.output)
    
    # Test specific dashboard
    if args.test_dashboard:
        test_dashboard(fetcher, args.test_dashboard, logger)
    
    # Test index search
    if args.test_index_search:
        test_index_search(fetcher, args.test_index_search, logger)
    
    logger.info("\n" + "=" * 80)
    logger.info("✓ TESTS COMPLETED")
    logger.info("=" * 80)
    
    return 0

def test_connection(fetcher, logger):
    """Test basic connection to Kibana"""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING CONNECTION")
    logger.info("=" * 80)
    
    success = fetcher.test_connection()
    
    if success:
        logger.info("✓ Connection successful!")
        
        # Try to get Kibana version
        try:
            url = f"{fetcher.kibana_url}/api/status"
            response = fetcher.session.get(url, verify=False, timeout=10)
            if response.status_code == 200:
                status = response.json()
                version = status.get('version', {}).get('number', 'Unknown')
                logger.info(f"✓ Kibana Version: {version}")
        except Exception as e:
            logger.debug(f"Could not get version: {e}")
    else:
        logger.error("✗ Connection failed!")
        return False
    
    return True

def list_index_patterns(fetcher, logger, output_file=None):
    """List all index patterns"""
    logger.info("\n" + "=" * 80)
    logger.info("LISTING INDEX PATTERNS")
    logger.info("=" * 80)
    
    url = f"{fetcher.kibana_url}/api/saved_objects/_find"
    params = {
        'type': 'index-pattern',
        'per_page': 100
    }
    
    try:
        response = fetcher.session.get(url, params=params, verify=False, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        saved_objects = data.get('saved_objects', [])
        
        logger.info(f"\nFound {len(saved_objects)} index patterns:")
        
        patterns = []
        for idx, obj in enumerate(saved_objects, 1):
            pattern_id = obj.get('id')
            pattern_title = obj.get('attributes', {}).get('title', 'Unknown')
            
            logger.info(f"\n[{idx}] {pattern_title}")
            logger.info(f"    ID: {pattern_id}")
            
            patterns.append({
                'id': pattern_id,
                'title': pattern_title
            })
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump({'index_patterns': patterns}, f, indent=2)
            logger.info(f"\n✓ Index patterns saved to: {output_file}")
        
        return patterns
        
    except Exception as e:
        logger.error(f"✗ Error listing index patterns: {e}")
        return []

def list_dashboards(fetcher, logger, output_file=None):
    """List all dashboards"""
    logger.info("\n" + "=" * 80)
    logger.info("LISTING DASHBOARDS")
    logger.info("=" * 80)
    
    url = f"{fetcher.kibana_url}/api/saved_objects/_find"
    params = {
        'type': 'dashboard',
        'per_page': 100
    }
    
    try:
        response = fetcher.session.get(url, params=params, verify=False, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        saved_objects = data.get('saved_objects', [])
        
        logger.info(f"\nFound {len(saved_objects)} dashboards:")
        
        dashboards = []
        for idx, obj in enumerate(saved_objects, 1):
            dash_id = obj.get('id')
            dash_title = obj.get('attributes', {}).get('title', 'Unknown')
            
            # Get panel count
            panels_json = obj.get('attributes', {}).get('panelsJSON', '[]')
            try:
                panels = json.loads(panels_json)
                panel_count = len(panels)
            except:
                panel_count = 0
            
            logger.info(f"\n[{idx}] {dash_title}")
            logger.info(f"    ID: {dash_id}")
            logger.info(f"    Panels: {panel_count}")
            
            dashboards.append({
                'id': dash_id,
                'title': dash_title,
                'panel_count': panel_count
            })
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump({'dashboards': dashboards}, f, indent=2)
            logger.info(f"\n✓ Dashboards saved to: {output_file}")
        
        return dashboards
        
    except Exception as e:
        logger.error(f"✗ Error listing dashboards: {e}")
        return []

def test_dashboard(fetcher, dash_id, logger):
    """Test fetching specific dashboard"""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING DASHBOARD FETCH")
    logger.info("=" * 80)
    logger.info(f"Dashboard ID: {dash_id}")
    
    dash_data = fetcher.get_dashboard_data(dash_id)
    
    if dash_data:
        logger.info("\n✓ Successfully fetched dashboard!")
        
        attributes = dash_data.get('attributes', {})
        logger.info(f"\nDashboard: {attributes.get('title', 'N/A')}")
        
        # Get panels
        panels_json = attributes.get('panelsJSON', '[]')
        try:
            panels = json.loads(panels_json)
            logger.info(f"Panels: {len(panels)}")
            
            for idx, panel in enumerate(panels[:5], 1):
                panel_type = panel.get('type', 'Unknown')
                logger.info(f"\n  [{idx}] Panel Type: {panel_type}")
                if 'id' in panel:
                    logger.info(f"      ID: {panel.get('id')}")
        except Exception as e:
            logger.warning(f"Could not parse panels: {e}")
    else:
        logger.error("✗ Failed to fetch dashboard")

def test_index_search(fetcher, index_name, logger):
    """Test searching an index"""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING INDEX SEARCH")
    logger.info("=" * 80)
    logger.info(f"Index: {index_name}")
    
    # Simple match-all query
    query = {
        "size": 10,
        "query": {
            "match_all": {}
        },
        "sort": [
            {"@timestamp": {"order": "desc"}}
        ]
    }
    
    logger.info("\nExecuting search...")
    result = fetcher.search_dashboard_metrics(index_name, query)
    
    if result:
        logger.info("✓ Search successful!")
        
        raw_response = result.get('rawResponse', {})
        hits = raw_response.get('hits', {})
        total_hits = hits.get('total', {}).get('value', 0)
        
        logger.info(f"\nTotal documents: {total_hits}")
        
        documents = hits.get('hits', [])
        logger.info(f"Retrieved: {len(documents)} documents")
        
        if documents:
            logger.info("\nSample Document:")
            sample = documents[0].get('_source', {})
            logger.info(json.dumps(sample, indent=2)[:500])
    else:
        logger.error("✗ Search failed")

if __name__ == '__main__':
    sys.exit(main())

