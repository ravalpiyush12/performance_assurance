"""
Monitoring Orchestrator - Coordinates data collection from all sources
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from threading import Thread, Event
from utils.logger import setup_logger

class MonitoringOrchestrator:
    """Orchestrates monitoring data collection from multiple sources"""
    
    def __init__(self, kibana_fetcher, appdynamics_fetcher, db_handler, config):
        """
        Initialize orchestrator
        
        Args:
            kibana_fetcher: KibanaDataFetcher instance
            appdynamics_fetcher: AppDynamicsDataFetcher instance
            db_handler: MonitoringDataDB instance
            config: MonitoringConfig instance
        """
        self.kibana_fetcher = kibana_fetcher
        self.appdynamics_fetcher = appdynamics_fetcher
        self.db_handler = db_handler
        self.config = config
        self.is_running = False
        self.stop_event = Event()
        self.test_run_id = None
        self.logger = setup_logger('MonitoringOrchestrator')
        
        # Store configuration from config object
        self.collection_interval = config.collection_interval
        self.enable_kibana = config.enable_kibana
        self.enable_appdynamics = config.enable_appdynamics
    
    def start_monitoring(self, test_run_id: str, duration_minutes: int, 
                        test_name: str = None, app_config: Dict = None):
        """
        Start monitoring for specified duration
        
        Args:
            test_run_id: Unique test run identifier
            duration_minutes: Total monitoring duration
            test_name: Optional test name
            app_config: Dictionary with app/tier/node names for AppDynamics
        """
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
        
        self.logger.info(f"=" * 80)
        self.logger.info(f"Starting Monitoring Session")
        self.logger.info(f"Test Run ID: {test_run_id}")
        self.logger.info(f"Duration: {duration_minutes} minutes")
        self.logger.info(f"Collection Interval: {self.collection_interval} seconds")
        self.logger.info(f"Kibana: {'Enabled' if self.enable_kibana else 'Disabled'}")
        self.logger.info(f"AppDynamics: {'Enabled' if self.enable_appdynamics else 'Disabled'}")
        self.logger.info(f"=" * 80)
        
        # Calculate iterations
        total_seconds = duration_minutes * 60
        iterations = total_seconds // self.collection_interval
        
        # Store app config
        self.app_config = app_config or {}
        
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
            self.logger.info(f"Monitoring Completed Successfully")
            self.logger.info(f"Total Collections: {collection_count}")
            self.logger.info(f"Test Run ID: {test_run_id}")
            self.logger.info(f"{'=' * 80}")
            
        except Exception as e:
            self.logger.error(f"Error during monitoring: {e}")
            self.db_handler.update_test_run_status(test_run_id, 'failed')
            raise
        finally:
            self.is_running = False
    
    def collect_all_data(self):
        """Collect data from all enabled sources"""
        timestamp = int(time.time() * 1000)
        collection_start = time.time()
        
        # Collect AppDynamics data
        if self.enable_appdynamics and self.appdynamics_fetcher:
            self._collect_appdynamics_data()
        
        # Collect Kibana data
        if self.enable_kibana and self.kibana_fetcher:
            self._collect_kibana_data(timestamp)
        
        collection_duration = time.time() - collection_start
        self.logger.info(f"Collection completed in {collection_duration:.2f} seconds")
    
    def _collect_appdynamics_data(self):
        """Collect AppDynamics metrics"""
        try:
            self.logger.info("→ Collecting AppDynamics metrics...")
            
            app_name = self.app_config.get('app_name', 'YourAppName')
            tier_name = self.app_config.get('tier_name', 'YourTier')
            node_name = self.app_config.get('node_name', 'YourNode')
            
            # Get all metrics (server, JVM, transactions)
            all_metrics = self.appdynamics_fetcher.get_all_metrics(
                app_name=app_name,
                tier_name=tier_name,
                node_name=node_name,
                duration_mins=5
            )
            
            # Count total data points
            total_points = 0
            for category, metrics in all_metrics.items():
                for metric_name, values in metrics.items():
                    total_points += len(values)
            
            if total_points > 0:
                # Insert into database
                self.db_handler.insert_appdynamics_metrics(
                    test_run_id=self.test_run_id,
                    app_name=app_name,
                    tier_name=tier_name,
                    node_name=node_name,
                    metrics_data=all_metrics
                )
                self.logger.info(f"  ✓ AppDynamics: {total_points} data points collected")
            else:
                self.logger.warning(f"  ⚠ AppDynamics: No data points returned")
            
        except Exception as e:
            self.logger.error(f"  ✗ AppDynamics collection error: {e}")
    
    def _collect_kibana_data(self, timestamp: int):
        """Collect Kibana visualization data"""
        try:
            self.logger.info("→ Collecting Kibana data...")
            
            visualizations = self.app_config.get('kibana_visualizations', [])
            
            if not visualizations:
                self.logger.warning("  ⚠ No Kibana visualizations configured")
                return
            
            total_viz_collected = 0
            
            for viz_config in visualizations:
                viz_id = viz_config.get('id')
                viz_name = viz_config.get('name', viz_id)
                
                try:
                    # Fetch visualization data
                    viz_data = self.kibana_fetcher.get_visualization_data(viz_id)
                    
                    if viz_data:
                        # Convert to list format for database
                        data_list = [viz_data]
                        
                        self.db_handler.insert_kibana_data(
                            test_run_id=self.test_run_id,
                            visualization_id=viz_id,
                            visualization_name=viz_name,
                            data=data_list,
                            timestamp=timestamp
                        )
                        total_viz_collected += 1
                        
                except Exception as e:
                    self.logger.error(f"  ✗ Error collecting visualization {viz_name}: {e}")
            
            if total_viz_collected > 0:
                self.logger.info(f"  ✓ Kibana: {total_viz_collected} visualizations collected")
            else:
                self.logger.warning(f"  ⚠ Kibana: No visualizations collected")
            
        except Exception as e:
            self.logger.error(f"  ✗ Kibana collection error: {e}")
    
    def stop_monitoring(self):
        """Stop the monitoring loop gracefully"""
        self.logger.info("Stop signal received...")
        self.is_running = False
        self.stop_event.set()
    
    def get_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'test_run_id': self.test_run_id,
            'kibana_enabled': self.enable_kibana,
            'appdynamics_enabled': self.enable_appdynamics,
            'collection_interval': self.collection_interval
        }