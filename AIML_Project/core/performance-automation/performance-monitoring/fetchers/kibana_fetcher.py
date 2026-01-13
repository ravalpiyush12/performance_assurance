"""
Kibana Data Fetcher using REST API
"""
import requests
import json
from typing import Dict, List, Optional
from utils.logger import setup_logger

class KibanaDataFetcher:
    """Fetch data from Kibana using REST API"""
    
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
    
    def get_visualization_data(self, visualization_id: str) -> Optional[Dict]:
        """
        Fetch data from a saved visualization
        
        Args:
            visualization_id: ID of the saved visualization
            
        Returns:
            Dictionary containing visualization data or None
        """
        url = f"{self.kibana_url}/api/saved_objects/visualization/{visualization_id}"
        
        try:
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"✓ Fetched visualization: {visualization_id}")
            return data
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"✗ HTTP error fetching visualization {visualization_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"✗ Error fetching visualization {visualization_id}: {e}")
            return None
    
    def search_index_data(self, index_pattern: str, query: Dict, time_field: str = '@timestamp') -> Optional[Dict]:
        """
        Search data from Elasticsearch index through Kibana
        
        Args:
            index_pattern: Index pattern to search
            query: Elasticsearch query DSL
            time_field: Time field name
            
        Returns:
            Search results or None
        """
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
            
            data = response.json()
            self.logger.info(f"✓ Search completed on index: {index_pattern}")
            return data
            
        except Exception as e:
            self.logger.error(f"✗ Error searching index {index_pattern}: {e}")
            return None
    
    def get_dashboard_data(self, dashboard_id: str) -> Optional[Dict]:
        """
        Get dashboard and all its visualizations
        
        Args:
            dashboard_id: ID of the dashboard
            
        Returns:
            Dashboard data or None
        """
        url = f"{self.kibana_url}/api/saved_objects/dashboard/{dashboard_id}"
        
        try:
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"✓ Fetched dashboard: {dashboard_id}")
            return data
            
        except Exception as e:
            self.logger.error(f"✗ Error fetching dashboard {dashboard_id}: {e}")
            return None
    
    def export_dashboard(self, dashboard_id: str) -> Optional[Dict]:
        """
        Export dashboard with all visualizations
        
        Args:
            dashboard_id: ID of the dashboard
            
        Returns:
            Exported dashboard data or None
        """
        url = f"{self.kibana_url}/api/kibana/dashboards/export"
        params = {'dashboard': dashboard_id}
        
        try:
            response = self.session.get(url, params=params, verify=False, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"✓ Exported dashboard: {dashboard_id}")
            return data
            
        except Exception as e:
            self.logger.error(f"✗ Error exporting dashboard {dashboard_id}: {e}")
            return None
    
    def get_index_pattern_fields(self, index_pattern_id: str) -> Optional[List[Dict]]:
        """
        Get fields from an index pattern
        
        Args:
            index_pattern_id: ID of the index pattern
            
        Returns:
            List of fields or None
        """
        url = f"{self.kibana_url}/api/saved_objects/index-pattern/{index_pattern_id}"
        
        try:
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            fields = json.loads(data.get('attributes', {}).get('fields', '[]'))
            self.logger.info(f"✓ Fetched {len(fields)} fields from index pattern: {index_pattern_id}")
            return fields
            
        except Exception as e:
            self.logger.error(f"✗ Error fetching index pattern {index_pattern_id}: {e}")
            return None
    
    def custom_query(self, index: str, query_body: Dict) -> Optional[Dict]:
        """
        Execute custom Elasticsearch query
        
        Args:
            index: Index name or pattern
            query_body: Complete Elasticsearch query body
            
        Returns:
            Query results or None
        """
        url = f"{self.kibana_url}/internal/search/es"
        
        payload = {
            "params": {
                "index": index,
                "body": query_body
            }
        }
        
        try:
            response = self.session.post(url, json=payload, verify=False, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            hits = data.get('rawResponse', {}).get('hits', {}).get('total', {}).get('value', 0)
            self.logger.info(f"✓ Custom query executed: {hits} hits")
            return data
            
        except Exception as e:
            self.logger.error(f"✗ Error executing custom query: {e}")
            return None
    
    def get_time_series_data(self, index: str, metric_field: str, 
                            time_field: str = '@timestamp', 
                            interval: str = '1m',
                            last_n_minutes: int = 5) -> Optional[Dict]:
        """
        Get time series aggregation data
        
        Args:
            index: Index name or pattern
            metric_field: Field to aggregate
            time_field: Timestamp field
            interval: Time interval for aggregation
            last_n_minutes: Look back period
            
        Returns:
            Time series data or None
        """
        query_body = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                time_field: {
                                    "gte": f"now-{last_n_minutes}m",
                                    "lte": "now"
                                }
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "time_buckets": {
                    "date_histogram": {
                        "field": time_field,
                        "fixed_interval": interval
                    },
                    "aggs": {
                        "avg_value": {
                            "avg": {
                                "field": metric_field
                            }
                        },
                        "max_value": {
                            "max": {
                                "field": metric_field
                            }
                        },
                        "min_value": {
                            "min": {
                                "field": metric_field
                            }
                        }
                    }
                }
            }
        }
        
        return self.custom_query(index, query_body)