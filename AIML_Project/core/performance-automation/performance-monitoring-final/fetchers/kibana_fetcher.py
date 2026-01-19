"""
Kibana Data Fetcher - Enhanced for Dashboard Metrics with Debug Output
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
    
    def print_dashboard_structure(self, dashboard_id: str, output_file: str = None):
        """
        Print complete dashboard structure to help identify field names
        
        Args:
            dashboard_id: Dashboard ID to inspect
            output_file: Optional file to save the output
        """
        self.logger.info("=" * 80)
        self.logger.info(f"DASHBOARD STRUCTURE ANALYSIS")
        self.logger.info("=" * 80)
        self.logger.info(f"Dashboard ID: {dashboard_id}")
        self.logger.info("=" * 80)
        
        # Get dashboard data
        dashboard = self.get_dashboard_data(dashboard_id)
        
        if not dashboard:
            self.logger.error("✗ Could not fetch dashboard")
            return None
        
        # Save raw JSON
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(dashboard, f, indent=2)
            self.logger.info(f"\n✓ Raw dashboard JSON saved to: {output_file}")
        
        # Parse and display structure
        attributes = dashboard.get('attributes', {})
        dash_title = attributes.get('title', 'Unknown')
        
        self.logger.info(f"\nDashboard Title: {dash_title}")
        self.logger.info(f"Dashboard ID: {dashboard_id}")
        
        # Get panels
        panels_json = attributes.get('panelsJSON', '[]')
        try:
            panels = json.loads(panels_json)
            self.logger.info(f"\nTotal Panels: {len(panels)}")
            
            # Analyze each panel
            for idx, panel in enumerate(panels, 1):
                self.logger.info("\n" + "-" * 80)
                self.logger.info(f"PANEL {idx}")
                self.logger.info("-" * 80)
                
                panel_type = panel.get('type', 'Unknown')
                panel_id = panel.get('id', 'N/A')
                
                self.logger.info(f"Type: {panel_type}")
                self.logger.info(f"ID: {panel_id}")
                
                # Print all panel keys
                self.logger.info(f"\nPanel Keys: {list(panel.keys())}")
                
                # Get visualization if available
                if panel_id != 'N/A':
                    viz_data = self.get_visualization_data(panel_id)
                    if viz_data:
                        self.logger.info("\n  Visualization Details:")
                        viz_attrs = viz_data.get('attributes', {})
                        
                        self.logger.info(f"    Title: {viz_attrs.get('title', 'N/A')}")
                        self.logger.info(f"    Type: {viz_attrs.get('type', 'N/A')}")
                        
                        # Get visualization state
                        vis_state = viz_attrs.get('visState')
                        if vis_state:
                            try:
                                state = json.loads(vis_state) if isinstance(vis_state, str) else vis_state
                                self.logger.info(f"\n    Visualization State Keys: {list(state.keys())}")
                                
                                # Print aggregations if available
                                aggs = state.get('aggs', [])
                                if aggs:
                                    self.logger.info(f"\n    Aggregations ({len(aggs)}):")
                                    for agg_idx, agg in enumerate(aggs, 1):
                                        self.logger.info(f"\n      [{agg_idx}] {agg.get('type', 'N/A')}")
                                        self.logger.info(f"          Schema: {agg.get('schema', 'N/A')}")
                                        self.logger.info(f"          ID: {agg.get('id', 'N/A')}")
                                        
                                        params = agg.get('params', {})
                                        if params:
                                            self.logger.info(f"          Params: {json.dumps(params, indent=10)}")
                                
                                # Print params
                                params = state.get('params', {})
                                if params:
                                    self.logger.info(f"\n    Visualization Params:")
                                    self.logger.info(f"      {json.dumps(params, indent=6)}")
                            
                            except Exception as e:
                                self.logger.warning(f"    Could not parse visState: {e}")
                        
                        # Get kibanaSavedObjectMeta
                        search_source = viz_attrs.get('kibanaSavedObjectMeta', {}).get('searchSourceJSON')
                        if search_source:
                            try:
                                search = json.loads(search_source) if isinstance(search_source, str) else search_source
                                self.logger.info(f"\n    Search Source:")
                                
                                # Index pattern
                                index = search.get('index', 'N/A')
                                self.logger.info(f"      Index: {index}")
                                
                                # Query
                                query = search.get('query', {})
                                if query:
                                    self.logger.info(f"      Query: {json.dumps(query, indent=8)}")
                                
                                # Filter
                                filter_data = search.get('filter', [])
                                if filter_data:
                                    self.logger.info(f"      Filters: {json.dumps(filter_data, indent=8)}")
                            
                            except Exception as e:
                                self.logger.warning(f"    Could not parse searchSource: {e}")
        
        except Exception as e:
            self.logger.error(f"Error parsing dashboard: {e}")
            return None
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("DASHBOARD ANALYSIS COMPLETE")
        self.logger.info("=" * 80)
        
        return dashboard
    
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
    
    def analyze_index_fields(self, index_pattern: str):
        """
        Analyze fields available in an index pattern
        
        Args:
            index_pattern: Index pattern to analyze
        """
        self.logger.info("=" * 80)
        self.logger.info(f"INDEX PATTERN ANALYSIS: {index_pattern}")
        self.logger.info("=" * 80)
        
        # Get index pattern info
        url = f"{self.kibana_url}/api/saved_objects/_find"
        params = {
            'type': 'index-pattern',
            'search_fields': 'title',
            'search': index_pattern,
            'per_page': 100
        }
        
        try:
            response = self.session.get(url, params=params, verify=False, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            saved_objects = data.get('saved_objects', [])
            
            if not saved_objects:
                self.logger.warning(f"No index pattern found matching: {index_pattern}")
                return
            
            for obj in saved_objects:
                pattern_title = obj.get('attributes', {}).get('title', 'Unknown')
                fields_json = obj.get('attributes', {}).get('fields', '[]')
                
                self.logger.info(f"\nIndex Pattern: {pattern_title}")
                
                try:
                    fields = json.loads(fields_json)
                    self.logger.info(f"Total Fields: {len(fields)}")
                    
                    # Group fields by type
                    field_types = {}
                    for field in fields:
                        field_name = field.get('name', 'unknown')
                        field_type = field.get('type', 'unknown')
                        
                        if field_type not in field_types:
                            field_types[field_type] = []
                        field_types[field_type].append(field_name)
                    
                    # Print fields by type
                    for field_type, field_names in sorted(field_types.items()):
                        self.logger.info(f"\n{field_type.upper()} Fields ({len(field_names)}):")
                        for field_name in sorted(field_names):
                            self.logger.info(f"  - {field_name}")
                    
                    # Highlight potential API/status/response time fields
                    self.logger.info("\n" + "-" * 80)
                    self.logger.info("SUGGESTED FIELDS FOR API MONITORING:")
                    self.logger.info("-" * 80)
                    
                    potential_api_fields = [f for f in field_names if any(
                        keyword in f.lower() for keyword in ['api', 'endpoint', 'url', 'path', 'service', 'method']
                    )]
                    if potential_api_fields:
                        self.logger.info("\nPotential API/Endpoint Fields:")
                        for f in potential_api_fields:
                            self.logger.info(f"  - {f}")
                    
                    potential_status_fields = [f for f in field_names if any(
                        keyword in f.lower() for keyword in ['status', 'result', 'outcome', 'success', 'fail']
                    )]
                    if potential_status_fields:
                        self.logger.info("\nPotential Status Fields:")
                        for f in potential_status_fields:
                            self.logger.info(f"  - {f}")
                    
                    potential_response_fields = [f for f in field_names if any(
                        keyword in f.lower() for keyword in ['response', 'duration', 'time', 'latency', 'elapsed']
                    )]
                    if potential_response_fields:
                        self.logger.info("\nPotential Response Time Fields:")
                        for f in potential_response_fields:
                            self.logger.info(f"  - {f}")
                
                except Exception as e:
                    self.logger.error(f"Error parsing fields: {e}")
        
        except Exception as e:
            self.logger.error(f"Error analyzing index: {e}")
    
    def test_query_with_fields(self, index_pattern: str, 
                               api_field: str,
                               status_field: str,
                               response_field: str,
                               time_field: str = "@timestamp"):
        """
        Test a query with specified field names to verify they work
        
        Args:
            index_pattern: Index pattern to query
            api_field: Field name for API/endpoint
            status_field: Field name for status
            response_field: Field name for response time
            time_field: Timestamp field
        """
        self.logger.info("=" * 80)
        self.logger.info("TESTING QUERY WITH SPECIFIED FIELDS")
        self.logger.info("=" * 80)
        self.logger.info(f"Index Pattern: {index_pattern}")
        self.logger.info(f"API Field: {api_field}")
        self.logger.info(f"Status Field: {status_field}")
        self.logger.info(f"Response Field: {response_field}")
        self.logger.info(f"Time Field: {time_field}")
        self.logger.info("=" * 80)
        
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                time_field: {
                                    "gte": "now-15m",
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
                        "size": 10
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
                        "response_stats": {
                            "stats": {
                                "field": response_field
                            }
                        },
                        "response_percentiles": {
                            "percentiles": {
                                "field": response_field,
                                "percents": [50, 90, 95, 99]
                            }
                        }
                    }
                }
            }
        }
        
        self.logger.info("\nQuery:")
        self.logger.info(json.dumps(query, indent=2))
        
        try:
            result = self.search_dashboard_metrics(index_pattern, query)
            
            if result:
                self.logger.info("\n✓ Query executed successfully!")
                
                raw_response = result.get('rawResponse', {})
                
                # Print total hits
                total_hits = raw_response.get('hits', {}).get('total', {})
                self.logger.info(f"\nTotal Documents Matched: {total_hits.get('value', 0)}")
                
                # Print aggregations
                aggregations = raw_response.get('aggregations', {})
                
                if 'by_api' in aggregations:
                    buckets = aggregations['by_api'].get('buckets', [])
                    self.logger.info(f"\nAPI Buckets Found: {len(buckets)}")
                    
                    for bucket in buckets:
                        api_name = bucket.get('key')
                        doc_count = bucket.get('doc_count', 0)
                        
                        pass_count = bucket.get('pass_count', {}).get('doc_count', 0)
                        fail_count = bucket.get('fail_count', {}).get('doc_count', 0)
                        
                        response_stats = bucket.get('response_stats', {})
                        percentiles = bucket.get('response_percentiles', {}).get('values', {})
                        
                        self.logger.info("\n" + "-" * 80)
                        self.logger.info(f"API: {api_name}")
                        self.logger.info(f"  Total Calls: {doc_count}")
                        self.logger.info(f"  Pass Count: {pass_count}")
                        self.logger.info(f"  Fail Count: {fail_count}")
                        self.logger.info(f"  Response Time Stats:")
                        self.logger.info(f"    Min: {response_stats.get('min', 'N/A')}")
                        self.logger.info(f"    Max: {response_stats.get('max', 'N/A')}")
                        self.logger.info(f"    Avg: {response_stats.get('avg', 'N/A')}")
                        self.logger.info(f"  Response Time Percentiles:")
                        self.logger.info(f"    P50: {percentiles.get('50.0', 'N/A')}")
                        self.logger.info(f"    P90: {percentiles.get('90.0', 'N/A')}")
                        self.logger.info(f"    P95: {percentiles.get('95.0', 'N/A')}")
                        self.logger.info(f"    P99: {percentiles.get('99.0', 'N/A')}")
                    
                    self.logger.info("\n" + "=" * 80)
                    self.logger.info("✓ FIELD MAPPING VERIFIED!")
                    self.logger.info("=" * 80)
                    self.logger.info("\nYou can use these field names in your configuration:")
                    self.logger.info(f"  --kibana-api-field \"{api_field}\"")
                    self.logger.info(f"  --kibana-status-field \"{status_field}\"")
                    self.logger.info(f"  --kibana-response-field \"{response_field}\"")
                    self.logger.info(f"  --kibana-timestamp-field \"{time_field}\"")
                else:
                    self.logger.warning("\n⚠ No aggregation results found")
                    self.logger.info("\nRaw Response:")
                    self.logger.info(json.dumps(raw_response, indent=2))
            else:
                self.logger.error("✗ Query failed")
        
        except Exception as e:
            self.logger.error(f"✗ Error executing query: {e}")
    
    def search_dashboard_metrics(self, index_pattern: str, query: Dict) -> Optional[Dict]:
        """
        Search metrics from Elasticsearch index
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