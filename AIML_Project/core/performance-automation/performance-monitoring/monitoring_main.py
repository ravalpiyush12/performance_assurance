#!/usr/bin/env python3
"""
Main entry point for monitoring data collection
"""
import argparse
import sys
import os
from datetime import datetime
from config.config import KibanaConfig, AppDynamicsConfig, DatabaseConfig, MonitoringConfig
from fetchers.kibana_fetcher import KibanaDataFetcher
from fetchers.appdynamics_fetcher import AppDynamicsDataFetcher
from database.db_handler import MonitoringDataDB
from orchestrator.monitoring_orchestrator import MonitoringOrchestrator
from utils.logger import setup_logger

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Performance Monitoring Data Collection')
    
    # Test configuration
    parser.add_argument('--run-id', required=True, help='Test Run ID')
    parser.add_argument('--test-name', help='Test name')
    parser.add_argument('--duration', type=int, required=True, help='Duration in minutes')
    
    # Kibana configuration
    parser.add_argument('--kibana-url', required=True, help='Kibana URL')
    parser.add_argument('--kibana-user', required=True, help='Kibana username')
    parser.add_argument('--kibana-pass', required=True, help='Kibana password')
    parser.add_argument('--kibana-viz-ids', help='Comma-separated visualization IDs')
    
    # AppDynamics configuration
    parser.add_argument('--appd-controller', required=True, help='AppDynamics controller URL')
    parser.add_argument('--appd-account', required=True, help='AppDynamics account name')
    parser.add_argument('--appd-user', required=True, help='AppDynamics username')
    parser.add_argument('--appd-pass', required=True, help='AppDynamics password')
    parser.add_argument('--appd-app', required=True, help='AppDynamics application name')
    parser.add_argument('--appd-tier', required=True, help='AppDynamics tier name')
    parser.add_argument('--appd-node', required=True, help='AppDynamics node name')
    
    # Oracle Database configuration
    parser.add_argument('--db-user', required=True, help='Oracle username')
    parser.add_argument('--db-pass', required=True, help='Oracle password')
    parser.add_argument('--db-dsn', required=True, help='Oracle DSN (host:port/service_name)')
    
    # Optional configuration
    parser.add_argument('--collection-interval', type=int, default=300, 
                       help='Collection interval in seconds (default: 300)')
    parser.add_argument('--disable-kibana', action='store_true', 
                       help='Disable Kibana data collection')
    parser.add_argument('--disable-appdynamics', action='store_true', 
                       help='Disable AppDynamics data collection')
    
    return parser.parse_args()

def main():
    """Main execution function"""
    args = parse_arguments()
    
    # Setup logger
    log_file = f"monitoring_{args.run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = setup_logger('MainMonitoring', log_file=log_file)
    
    logger.info("=" * 80)
    logger.info("Performance Monitoring System - Starting")
    logger.info("=" * 80)
    
    try:
        # Initialize database
        logger.info("Initializing Oracle database connection...")
        db_handler = MonitoringDataDB(
            username=args.db_user,
            password=args.db_pass,
            dsn=args.db_dsn
        )
        
        # Initialize Kibana fetcher
        kibana_fetcher = None
        if not args.disable_kibana:
            logger.info("Initializing Kibana fetcher...")
            kibana_fetcher = KibanaDataFetcher(
                kibana_url=args.kibana_url,
                username=args.kibana_user,
                password=args.kibana_pass
            )
            if not kibana_fetcher.test_connection():
                logger.warning("Kibana connection test failed - continuing anyway")
        
        # Initialize AppDynamics fetcher
        appdynamics_fetcher = None
        if not args.disable_appdynamics:
            logger.info("Initializing AppDynamics fetcher...")
            appdynamics_fetcher = AppDynamicsDataFetcher(
                controller_url=args.appd_controller,
                account_name=args.appd_account,
                username=args.appd_user,
                password=args.appd_pass
            )
            if not appdynamics_fetcher.test_connection():
                logger.warning("AppDynamics connection test failed - continuing anyway")
        
        # Create monitoring configuration
        monitoring_config = MonitoringConfig(
            collection_interval=args.collection_interval,
            test_duration=args.duration * 60,
            enable_kibana=not args.disable_kibana,
            enable_appdynamics=not args.disable_appdynamics
        )
        
        # Parse visualization IDs
        kibana_visualizations = []
        if args.kibana_viz_ids:
            for viz_id in args.kibana_viz_ids.split(','):
                viz_id = viz_id.strip()
                kibana_visualizations.append({
                    'id': viz_id,
                    'name': f'Visualization_{viz_id}'
                })
        
        # Application configuration
        app_config = {
            'app_name': args.appd_app,
            'tier_name': args.appd_tier,
            'node_name': args.appd_node,
            'kibana_visualizations': kibana_visualizations
        }
        
        # Create orchestrator
        logger.info("Creating monitoring orchestrator...")
        orchestrator = MonitoringOrchestrator(
            kibana_fetcher=kibana_fetcher,
            appdynamics_fetcher=appdynamics_fetcher,
            db_handler=db_handler,
            config=monitoring_config
        )
        
        # Start monitoring
        logger.info("Starting monitoring session...")
        orchestrator.start_monitoring(
            test_run_id=args.run_id,
            duration_minutes=args.duration,
            test_name=args.test_name,
            app_config=app_config
        )
        
        logger.info("=" * 80)
        logger.info("Monitoring completed successfully!")
        logger.info(f"Test Run ID: {args.run_id}")
        logger.info("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nMonitoring interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
        
    finally:
        # Cleanup
        if 'db_handler' in locals():
            db_handler.close()
        logger.info("Cleanup completed")

if __name__ == '__main__':
    sys.exit(main())