"""
Monitoring Orchestrator - Coordinates all data collection
"""
import time
from datetime import datetime
from typing import Dict
from threading import Event
from utils.logger import setup_logger

class MonitoringOrchestrator:
    """Orchestrates monitoring data collection"""
    
    def __init__(self, kibana_fetcher, appdynamics_fetcher, db_handler, config):
        self.kibana_fetcher = kibana_fetcher
        self.appdynamics_fetcher = appdynamics_fetcher
        self.db_handler = db_handler
        self.config = config
        self.is_running = False
        self.stop_event = Event()
        self.test_run_id = None
        self.logger = setup_logger('MonitoringOrchestrator')
        
        self.collection_interval = config.collection_interval
        self.enable_kibana = config.enable_kibana
        self.enable_appdynamics = config.enable_appdynamics
    
    def start_monitoring(self, test_run_id: str, duration_minutes: int, 
                        test_name: str = None, app_config: Dict = None):
        """Start monitoring for specified duration"""
        self.test_run_id = test_run_id
        self.is_running = True
        self.stop_event.clear()
        
        # Insert test run record
        self.db_handler.insert_test_run(
            test_run_id=test_run_id,
            test_name=test_name,
            start_time=datetime.now(),
            duration_minutes=duration_minutes
        )
        
        self.logger.info("=" * 80)
        self.logger.info("Starting Monitoring Session")
        self.logger.info(f"Test Run ID: {test_run_id}")
        self.logger.info(f"Duration: {duration_minutes} minutes")
        self.logger.info(f"Collection Interval: {self.collection_interval} seconds (5 minutes)")
        self.logger.info("=" * 80)
        
        # Store configurations
        self.appd_apps = app_config.get('appdynamics_apps', [])
        self.kibana_dashboards = app_config.get('kibana_dashboards', [])
        self.kibana_index_pattern = app_config.get('kibana_index_pattern', 'your-index-*')
        self.kibana_field_config = app_config.get('kibana_fields', {})
        
        # Calculate iterations
        total_seconds = duration_minutes * 60
        iterations = total_seconds // self.collection_interval
        
        collection_count = 0
        start_time = time.time()
        
        try:
            for i in range(int(iterations)):
                if self.stop_event.is_set():
                    self.logger.info("Monitoring stopped by user")
                    break
                
                elapsed_minutes = (time.time() - start_time) / 60
                remaining_minutes = duration_minutes - elapsed_minutes
                
                self.logger.info(f"\n{'=' * 80}")
                self.logger.info(f"Collection #{i+1}/{int(iterations)} - Elapsed: {elapsed_minutes:.1f}m - Remaining: {remaining_minutes:.1f}m")
                self.logger.info(f"{'=' * 80}")
                
                # Collect data
                self.collect_all_data()
                collection_count += 1
                
                # Wait for next iteration
                if i < iterations - 1:
                    self.logger.info(f"Waiting {self.collection_interval} seconds until next collection...")
                    if self.stop_event.wait(timeout=self.collection_interval):
                        break
            
            # Update test run status
            self.db_handler.update_test_run_status(test_run_id, 'completed')
            
            self.logger.info(f"\n{'=' * 80}")
            self.logger.info("Monitoring Completed Successfully")
            self.logger.info(f"Total Collections: {collection_count}")
            self.logger.info("=" * 80)
            
        except Exception as e:
            self.logger.error(f"Error during monitoring: {e}")
            self.db_handler.update_test_run_status(test_run_id, 'failed')
            raise
        finally:
            self.is_running = False
    
    def collect_all_data(self):
        """Collect data from all sources"""
        collection_start = time.time()
        
        # Collect AppDynamics data
        if self.enable_appdynamics and self.appdynamics_fetcher:
            self._collect_appdynamics_data()
        
        # Collect Kibana data
        if self.enable_kibana and self.kibana_fetcher:
            self._collect_kibana_data()
        
        collection_duration = time.time() - collection_start
        self.logger.info(f"\n✓ Collection completed in {collection_duration:.2f} seconds")
    
    def _collect_appdynamics_data(self):
        """Collect AppDynamics metrics"""
        try:
            self.logger.info("\n→ Collecting AppDynamics metrics...")
            
            if not self.appd_apps:
                self.logger.warning("  ⚠ No AppDynamics configuration provided")
                return
            
            # Collect all metrics
            all_metrics = self.appdynamics_fetcher.collect_all_metrics(
                app_configs=self.appd_apps,
                duration_mins=5
            )
            
            total_points = self.appdynamics_fetcher._count_total_data_points(all_metrics)
            
            if total_points > 0:
                # Insert server metrics
                self.db_handler.insert_appd_server_metrics(
                    test_run_id=self.test_run_id,
                    metrics_data=all_metrics
                )
                
                # Insert JVM metrics
                self.db_handler.insert_appd_jvm_metrics(
                    test_run_id=self.test_run_id,
                    metrics_data=all_metrics
                )
                
                # Insert application metrics
                self.db_handler.insert_appd_application_metrics(
                    test_run_id=self.test_run_id,
                    metrics_data=all_metrics
                )
                
                self.logger.info(f"  ✓ AppDynamics: {total_points} data points collected")
            else:
                self.logger.warning(f"  ⚠ AppDynamics: No data points returned")
            
        except Exception as e:
            self.logger.error(f"  ✗ AppDynamics collection error: {e}")
    
    def _collect_kibana_data(self):
        """Collect Kibana dashboard metrics"""
        try:
            self.logger.info("\n→ Collecting Kibana metrics...")
            
            if not self.kibana_dashboards:
                self.logger.warning("  ⚠ No Kibana dashboard configuration provided")
                return
            
            # Collect dashboard metrics
            dashboard_metrics = self.kibana_fetcher.collect_dashboard_metrics(
                dashboard_config=self.kibana_dashboards,
                index_pattern=self.kibana_index_pattern,
                api_field=self.kibana_field_config.get('api_field', 'api_name.keyword'),
                status_field=self.kibana_field_config.get('status_field', 'status'),
                response_time_field=self.kibana_field_config.get('response_time_field', 'response_time'),
                timestamp_field=self.kibana_field_config.get('timestamp_field', '@timestamp')
            )
            
            # Count total APIs
            total_apis = sum(
                len(dash_data.get('apis', [])) 
                for dash_data in dashboard_metrics.values()
            )
            
            if total_apis > 0:
                # Insert into database
                self.db_handler.insert_kibana_api_metrics(
                    test_run_id=self.test_run_id,
                    metrics_data=dashboard_metrics
                )
                
                self.logger.info(f"  ✓ Kibana: {total_apis} API metrics collected")
            else:
                self.logger.warning(f"  ⚠ Kibana: No API metrics returned")
            
        except Exception as e:
            self.logger.error(f"  ✗ Kibana collection error: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring gracefully"""
        self.logger.info("Stop signal received...")
        self.is_running = False
        self.stop_event.set()