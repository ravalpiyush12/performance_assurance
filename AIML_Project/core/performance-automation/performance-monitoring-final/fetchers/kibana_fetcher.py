"""
Kibana Data Fetcher - Enhanced for Dashboard Metrics
"""
import requests
import json
from typing import Dict, List, Optional
from utils.logger import setup_logger
import urllib3

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
    
    def search_dashboard_metrics(self, index_pattern: str, query: Dict) -> Optional[Dict]:
        """
        Search metrics from Elasticsearch index
        
        Example query for API metrics:
        {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"@timestamp": {"gte": "now-5m", "lte": "now"}}}
                    ]
                }
            },
            "aggs": {
                "by_api": {
                    "terms": {"field": "api_name.keyword", "size": 100},
                    "aggs": {
                        "total_count": {"value_count": {"field": "api_name.keyword"}},
                        "pass_count": {"filter": {"term": {"status": "pass"}}},
                        "fail_count": {"filter": {"term": {"status": "fail"}}},
                        "p90_response": {"percentiles": {"field": "response_time", "percents": [90]}},
                        "p95_response": {"percentiles": {"field": "response_time", "percents": [95]}}
                    }
                }
            }
        }
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
            return response.json()
        except Exception as e:
            self.logger.error(f"✗ Error searching metrics: {e}")
            return None
    
    def collect_dashboard_metrics(self, dashboard_config: List[Dict], 
                                  index_pattern: str,
                                  api_field: str = "api_name.keyword",
                                  status_field: str = "status",
                                  response_time_field: str = "response_time",
                                  timestamp_field: str = "@timestamp") -> Dict:
        """
        Collect metrics from dashboards
        
        Args:
            dashboard_config: List of dashboard configurations
            index_pattern: Elasticsearch index pattern
            api_field: Field name for API/endpoint
            status_field: Field name for status (pass/fail)
            response_time_field: Field name for response time
            timestamp_field: Timestamp field name
            
        Returns:
            Dictionary with collected metrics
        """
        all_metrics = {}
        
        self.logger.info("=" * 80)
        self.logger.info(f"Collecting Kibana Dashboard Metrics")
        self.logger.info("=" * 80)
        
        # Build aggregation query
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                timestamp_field: {
                                    "gte": "now-5m",
                                    "lte": "now"
                                }
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "by_api": {
                    "terms": {
                        "field": api_field,
                        "size": 1000
                    },
                    "aggs": {
                        "total_count": {
                            "value_count": {
                                "field": api_field
                            }
                        },
                        "pass_count": {
                            "filter": {
                                "term": {
                                    status_field: "pass"
                                }
                            }
                        },
                        "fail_count": {
                            "filter": {
                                "term": {
                                    status_field: "fail"
                                }
                            }
                        },
                        "p90_response": {
                            "percentiles": {
                                "field": response_time_field,
                                "percents": [90]
                            }
                        },
                        "p95_response": {
                            "percentiles": {
                                "field": response_time_field,
                                "percents": [95]
                            }
                        },
                        "avg_response": {
                            "avg": {
                                "field": response_time_field
                            }
                        },
                        "min_response": {
                            "min": {
                                "field": response_time_field
                            }
                        },
                        "max_response": {
                            "max": {
                                "field": response_time_field
                            }
                        }
                    }
                }
            }
        }
        
        for dash_idx, dashboard in enumerate(dashboard_config, 1):
            dash_id = dashboard.get('id')
            dash_name = dashboard.get('name', dash_id)
            
            self.logger.info(f"\n[{dash_idx}/{len(dashboard_config)}] {dash_name}")
            
            try:
                result = self.search_dashboard_metrics(index_pattern, query)
                
                if result:
                    raw_response = result.get('rawResponse', {})
                    aggregations = raw_response.get('aggregations', {})
                    
                    if 'by_api' in aggregations:
                        buckets = aggregations['by_api'].get('buckets', [])
                        
                        dashboard_metrics = {
                            'dashboard_id': dash_id,
                            'dashboard_name': dash_name,
                            'apis': []
                        }
                        
                        for bucket in buckets:
                            api_name = bucket.get('key')
                            total_count = bucket.get('doc_count', 0)
                            pass_count = bucket.get('pass_count', {}).get('doc_count', 0)
                            fail_count = bucket.get('fail_count', {}).get('doc_count', 0)
                            
                            p90_values = bucket.get('p90_response', {}).get('values', {})
                            p95_values = bucket.get('p95_response', {}).get('values', {})
                            
                            p90_response = p90_values.get('90.0', 0)
                            p95_response = p95_values.get('95.0', 0)
                            
                            avg_response = bucket.get('avg_response', {}).get('value', 0)
                            min_response = bucket.get('min_response', {}).get('value', 0)
                            max_response = bucket.get('max_response', {}).get('value', 0)
                            
                            api_metric = {
                                'api_name': api_name,
                                'total_count': total_count,
                                'pass_count': pass_count,
                                'fail_count': fail_count,
                                'p90_response_time': p90_response,
                                'p95_response_time': p95_response,
                                'avg_response_time': avg_response,
                                'min_response_time': min_response,
                                'max_response_time': max_response
                            }
                            
                            dashboard_metrics['apis'].append(api_metric)
                        
                        all_metrics[dash_name] = dashboard_metrics
                        
                        self.logger.info(f"  ✓ Collected metrics for {len(buckets)} APIs")
                    else:
                        self.logger.warning(f"  ⚠ No aggregation data found")
                else:
                    self.logger.warning(f"  ⚠ No results returned")
                    
            except Exception as e:
                self.logger.error(f"  ✗ Error collecting metrics: {e}")
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"Kibana Collection Complete")
        self.logger.info("=" * 80)
        
        return all_metrics