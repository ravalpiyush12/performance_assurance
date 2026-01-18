#!/usr/bin/env python3
"""
Main entry point for performance monitoring
"""
import argparse
import sys
import os
import json
from datetime import datetime
from config.config import MonitoringConfig
from fetchers.kibana_fetcher import KibanaDataFetcher
from fetchers.appdynamics_fetcher import AppDynamicsDataFetcher
from database.db_handler import MonitoringDataDB
from orchestrator.monitoring_orchestrator import MonitoringOrchestrator
from utils.logger import setup_logger
import os
from pathlib import Path

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Performance Monitoring System')
    
    # Test configuration
    parser.add_argument('--run-id', required=True, help='Test Run ID')
    parser.add_argument('--test-name', help='Test name')
    parser.add_argument('--duration', type=int, required=True, help='Duration in minutes')
    
    # AppDynamics configuration
    parser.add_argument('--appd-controller', required=True, help='AppDynamics controller URL')
    parser.add_argument('--appd-account', required=True, help='AppDynamics account name')
    parser.add_argument('--appd-user', required=True, help='AppDynamics username')
    parser.add_argument('--appd-pass', required=True, help='AppDynamics password')
    parser.add_argument('--appd-config', required=True, help='AppDynamics config JSON file')
    
    # Kibana configuration
    parser.add_argument('--kibana-url', required=True, help='Kibana URL')
    parser.add_argument('--kibana-user', required=True, help='Kibana username')
    parser.add_argument('--kibana-pass', required=True, help='Kibana password')
    parser.add_argument('--kibana-config', required=True, help='Kibana config JSON file')
    parser.add_argument('--kibana-index', default='your-index-*', help='Kibana index pattern')
    
    # Kibana field mappings
    parser.add_argument('--kibana-api-field', default='api_name.keyword', 
                       help='Field name for API/endpoint')
    parser.add_argument('--kibana-status-field', default='status', 
                       help='Field name for status (pass/fail)')
    parser.add_argument('--kibana-response-field', default='response_time', 
                       help='Field name for response time')
    parser.add_argument('--kibana-timestamp-field', default='@timestamp',
                       help='Field name for timestamp')
    
    # Oracle Database configuration
    parser.add_argument('--db-user', required=True, help='Oracle username')
    parser.add_argument('--db-pass', required=True, help='Oracle password')
    parser.add_argument('--db-dsn', required=True, help='Oracle DSN (host:port/service_name)')
    
    # Optional
    parser.add_argument('--disable-kibana', action='store_true', help='Disable Kibana')
    parser.add_argument('--disable-appdynamics', action='store_true', help='Disable AppDynamics')
    
    return parser.parse_args()

def load_json_config(config_file: str, config_type: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"✓ Loaded {config_type} configuration from {config_file}")
        return config
    except FileNotFoundError:
        print(f"✗ Configuration file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in {config_file}: {e}")
        sys.exit(1)

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
        # Load AppDynamics configuration
        appd_config = load_json_config(args.appd_config, 'AppDynamics')
        appd_apps = appd_config.get('applications', [])
        logger.info(f"AppDynamics: {len(appd_apps)} applications configured")
        
        # Load Kibana configuration
        kibana_config = load_json_config(args.kibana_config, 'Kibana')
        kibana_dashboards = kibana_config.get('dashboards', [])
        logger.info(f"Kibana: {len(kibana_dashboards)} dashboards configured")
        
        # Initialize database
        logger.info("\n→ Initializing Oracle database...")
        db_handler = MonitoringDataDB(
            username=args.db_user,
            password=args.db_pass,
            dsn=args.db_dsn
        )
        
        # Initialize Kibana fetcher
        kibana_fetcher = None
        if not args.disable_kibana:
            logger.info("\n→ Initializing Kibana...")
            kibana_fetcher = KibanaDataFetcher(
                kibana_url=args.kibana_url,
                username=args.kibana_user,
                password=args.kibana_pass
            )
            if not kibana_fetcher.test_connection():
                logger.warning("Kibana connection test failed")
        
        # Initialize AppDynamics fetcher
        appdynamics_fetcher = None
        if not args.disable_appdynamics:
            logger.info("\n→ Initializing AppDynamics...")
            appdynamics_fetcher = AppDynamicsDataFetcher(
                controller_url=args.appd_controller,
                account_name=args.appd_account,
                username=args.appd_user,
                password=args.appd_pass
            )
            if not appdynamics_fetcher.test_connection():
                logger.warning("AppDynamics connection test failed")
        
        # Create monitoring configuration
        monitoring_config = MonitoringConfig(
            collection_interval=300,  # 5 minutes
            test_duration=args.duration * 60,
            enable_kibana=not args.disable_kibana and kibana_fetcher is not None,
            enable_appdynamics=not args.disable_appdynamics
        )
        
        # Application configuration
        app_config = {
            'appdynamics_apps': appd_apps,
            'kibana_dashboards': kibana_dashboards,
            'kibana_index_pattern': args.kibana_index,
            'kibana_fields': {
                'api_field': args.kibana_api_field,
                'status_field': args.kibana_status_field,
                'response_time_field': args.kibana_response_field,
                'timestamp_field': args.kibana_timestamp_field
            }
        }
        
        # Create orchestrator
        logger.info("\n→ Creating monitoring orchestrator...")
        orchestrator = MonitoringOrchestrator(
            kibana_fetcher=kibana_fetcher,
            appdynamics_fetcher=appdynamics_fetcher,
            db_handler=db_handler,
            config=monitoring_config
        )
        
        # Start monitoring
        logger.info("\n→ Starting monitoring session...")
        orchestrator.start_monitoring(
            test_run_id=args.run_id,
            duration_minutes=args.duration,
            test_name=args.test_name,
            app_config=app_config
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ Monitoring Completed Successfully!")
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
        if 'db_handler' in locals():
            db_handler.close()
        logger.info("Cleanup completed")

# Add to top of monitoring_main.py, generate_appd_config.py, etc.



# Try to load .env file if it exists (for local development)
def load_env_file():
    """Load environment variables from .env file if present"""
    env_file = Path('.env')
    if env_file.exists():
        print("Loading .env file for local development...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        return True
    return False

# Call at the start of main()
if __name__ == '__main__':
    load_env_file()  # Load .env if running locally
    sys.exit(main())