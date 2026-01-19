"""
Kibana Data Fetcher - Customized for Table Dashboard
"""
import requests
import json
from typing import Dict, List, Optional
from utils.logger import setup_logger
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class KibanaDataFetcher:
    """Fetch dashboard data from Kibana"""
    
    def __init__(self, kibana_url: str, username: str, password: str):
        self.kibana_url = kibana_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth = (username, password)
        self.headers = {
            'kbn-xsrf': 'true',
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update(self.headers)
        self.logger = setup_logger('KibanaFetcher')
        
    def test_connection(self) -> bool:
        """Test connection to Kibana"""
        try:
            url = f"{self.kibana_url}/api/status"
            response = self.session.get(url, verify=False, timeout=10)
            if response.status_code == 200:
                self.logger.info("✓ Kibana connection successful")
                return True
            else:
                self.logger.error(f"✗ Kibana connection failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"✗ Kibana connection error: {e}")
            return False
    
    def get_dashboard_data(self, dashboard_id: str) -> Optional[Dict]:
        """Get dashboard metadata"""
        url = f"{self.kibana_url}/api/saved_objects/dashboard/{dashboard_id}"
        
        try:
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"✗ Error fetching dashboard {dashboard_id}: {e}")
            return None
    
    def extract_index_pattern_from_dashboard(self, dashboard_id: str) -> Optional[str]:
        """
        Extract index pattern from dashboard
        """
        dashboard = self.get_dashboard_data(dashboard_id)
        
        if not dashboard:
            return None
        
        try:
            # Get panels
            attributes = dashboard.get('attributes', {})
            panels_json = attributes.get('panelsJSON', '[]')
            panels = json.loads(panels_json)
            
            # Get first panel to find index pattern
            for panel in panels:
                panel_id = panel.get('id')
                if panel_id:
                    viz_data = self.get_visualization_data(panel_id)
                    if viz_data:
                        search_source = viz_data.get('attributes', {}).get('kibanaSavedObjectMeta', {}).get('searchSourceJSON', '{}')
                        search = json.loads(search_source)
                        index_id = search.get('index')
                        
                        if index_id:
                            # Get index pattern details
                            index_pattern = self.get_index_pattern(index_id)
                            if index_pattern:
                                return index_pattern.get('attributes', {}).get('title')
        except Exception as e:
            self.logger.error(f"Error extracting index pattern: {e}")
        
        return None
    
    def get_visualization_data(self, viz_id: str) -> Optional[Dict]:
        """Get visualization data"""
        url = f"{self.kibana_url}/api/saved_objects/visualization/{viz_id}"
        
        try:
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.debug(f"Could not fetch visualization {viz_id}: {e}")
            return None
    
    def get_index_pattern(self, index_id: str) -> Optional[Dict]:
        """Get index pattern details"""
        url = f"{self.kibana_url}/api/saved_objects/index-pattern/{index_id}"
        
        try:
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.debug(f"Could not fetch index pattern {index_id}: {e}")
            return None
    
    def fetch_dashboard_table_data(self, 
                                   index_pattern: str,
                                   endpoint_field: str = "userRequestedUri.keyword",
                                   time_field: str = "@timestamp",
                                   time_range_minutes: int = 5) -> List[Dict]:
        """
        Fetch data matching your dashboard table structure
        
        Args:
            index_pattern: Elasticsearch index pattern
            endpoint_field: Field containing API endpoint
            time_field: Timestamp field
            time_range_minutes: Time range to query
            
        Returns:
            List of API metrics matching your dashboard
        """
        
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                time_field: {
                                    "gte": f"now-{time_range_minutes}m",
                                    "lte": "now"
                                }
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "endpoints": {
                    "terms": {
                        "field": endpoint_field,
                        "size": 1000,
                        "order": {
                            "_count": "desc"
                        }
                    },
                    "aggs": {
                        "pass_count": {
                            "filter": {
                                "term": {
                                    "responseCode": 200
                                }
                            }
                        },
                        "fail_count": {
                            "filter": {
                                "bool": {
                                    "must_not": {
                                        "term": {
                                            "responseCode": 200
                                        }
                                    }
                                }
                            }
                        },
                        "response_time_stats": {
                            "stats": {
                                "field": "duration"
                            }
                        },
                        "response_time_percentiles": {
                            "percentiles": {
                                "field": "duration",
                                "percents": [90, 95]
                            }
                        }
                    }
                }
            }
        }
        
        try:
            result = self.search_index(index_pattern, query)
            
            if result:
                return self._parse_table_results(result)
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching dashboard data: {e}")
            return []
    
    def _parse_table_results(self, result: Dict) -> List[Dict]:
        """Parse aggregation results into table format"""
        
        api_metrics = []
        
        try:
            raw_response = result.get('rawResponse', {})
            aggregations = raw_response.get('aggregations', {})
            
            buckets = aggregations.get('endpoints', {}).get('buckets', [])
            
            for bucket in buckets:
                endpoint = bucket.get('key', '')
                total_requests = bucket.get('doc_count', 0)
                
                pass_count = bucket.get('pass_count', {}).get('doc_count', 0)
                fail_count = bucket.get('fail_count', {}).get('doc_count', 0)
                
                stats = bucket.get('response_time_stats', {})
                percentiles = bucket.get('response_time_percentiles', {}).get('values', {})
                
                api_metric = {
                    'api_endpoint': endpoint,
                    'total_requests': total_requests,
                    'pass_count': pass_count,
                    'fail_count': fail_count,
                    'min_response_time': stats.get('min', 0),
                    'avg_response_time': stats.get('avg', 0),
                    'max_response_time': stats.get('max', 0),
                    'p90_response_time': percentiles.get('90.0', 0),
                    'p95_response_time': percentiles.get('95.0', 0)
                }
                
                api_metrics.append(api_metric)
            
            self.logger.info(f"Parsed {len(api_metrics)} API endpoints")
            
        except Exception as e:
            self.logger.error(f"Error parsing results: {e}")
        
        return api_metrics
    
    def search_index(self, index_pattern: str, query: Dict) -> Optional[Dict]:
        """Search Elasticsearch index"""
        url = f"{self.kibana_url}/internal/search/es"
        
        payload = {
            "params": {
                "index": index_pattern,
                "body": query
            }
        }
        
        try:
            response = self.session.post(url, json=payload, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"✗ Error searching index: {e}")
            return None
    
    def collect_dashboard_metrics(self, 
                                  dashboard_config: List[Dict],
                                  index_pattern: str,
                                  endpoint_field: str = "userRequestedUri.keyword",
                                  time_field: str = "@timestamp") -> Dict:
        """
        Collect metrics from dashboards every 5 minutes
        
        Args:
            dashboard_config: List of dashboard configurations
            index_pattern: Index pattern to query
            endpoint_field: Field containing endpoint/URI
            time_field: Timestamp field
            
        Returns:
            Dictionary with collected metrics
        """
        all_metrics = {}
        
        self.logger.info("=" * 80)
        self.logger.info(f"Collecting Kibana Dashboard Metrics")
        self.logger.info("=" * 80)
        
        for dash_idx, dashboard in enumerate(dashboard_config, 1):
            dash_id = dashboard.get('id')
            dash_name = dashboard.get('name', dash_id)
            
            self.logger.info(f"\n[{dash_idx}/{len(dashboard_config)}] {dash_name}")
            
            try:
                # Fetch table data
                api_metrics = self.fetch_dashboard_table_data(
                    index_pattern=index_pattern,
                    endpoint_field=endpoint_field,
                    time_field=time_field,
                    time_range_minutes=5
                )
                
                if api_metrics:
                    dashboard_metrics = {
                        'dashboard_id': dash_id,
                        'dashboard_name': dash_name,
                        'apis': api_metrics
                    }
                    
                    all_metrics[dash_name] = dashboard_metrics
                    
                    self.logger.info(f"  ✓ Collected metrics for {len(api_metrics)} API endpoints")
                    
                    # Log summary
                    total_requests = sum(api.get('total_requests', 0) for api in api_metrics)
                    total_pass = sum(api.get('pass_count', 0) for api in api_metrics)
                    total_fail = sum(api.get('fail_count', 0) for api in api_metrics)
                    
                    self.logger.info(f"  Total Requests: {total_requests}")
                    self.logger.info(f"  Pass: {total_pass}, Fail: {total_fail}")
                else:
                    self.logger.warning(f"  ⚠ No data returned")
                    
            except Exception as e:
                self.logger.error(f"  ✗ Error collecting metrics: {e}")
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"Kibana Collection Complete")
        self.logger.info("=" * 80)
        
        return all_metrics