from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch
import re
from datetime import datetime, timedelta

app = Flask(__name__)

# CONFIGURE YOUR ELASTICSEARCH CONNECTION HERE
ES_CONFIG = {
    'hosts': ['http://localhost:9200'],
    'basic_auth': ('elastic', 'your_password'),  # Use if authentication is enabled
    # 'api_key': ('id', 'api_key'),  # Alternative: use API key authentication
}

# Index names for Production and PTE data
PROD_INDEX = 'prod-stats-*'  # Production statistics index pattern
PTE_INDEX = 'pte-metrics-*'   # PTE test metrics index pattern

class NLQueryProcessor:
    """Process natural language queries and convert to Elasticsearch queries"""
    
    def __init__(self):
        # Define query patterns and their Elasticsearch query templates
        self.patterns = {
            'payment_count_branch_peak': {
                'regex': r'(?:how many|count|total).*payment.*branch\s+(\d+).*(?:peak|busy)',
                'prod_query': {
                    'query': {
                        'bool': {
                            'must': [
                                {'term': {'branch_id': '{branch_id}'}},
                                {'term': {'txn_type': 'PAYMENT'}},
                                {'range': {
                                    'timestamp': {
                                        'gte': 'now-1d/d',
                                        'lte': 'now'
                                    }
                                }},
                                {'range': {
                                    'hour_of_day': {
                                        'gte': 9,
                                        'lte': 14
                                    }
                                }}
                            ]
                        }
                    },
                    'aggs': {
                        'payments_by_hour': {
                            'date_histogram': {
                                'field': 'timestamp',
                                'calendar_interval': 'hour'
                            },
                            'aggs': {
                                'payment_count': {'value_count': {'field': 'txn_id'}},
                                'success_rate': {
                                    'avg': {
                                        'script': "doc['status'].value == 'SUCCESS' ? 1 : 0"
                                    }
                                }
                            }
                        }
                    }
                },
                'pte_query': {
                    'query': {
                        'bool': {
                            'must': [
                                {'term': {'branch_id': '{branch_id}'}},
                                {'wildcard': {'test_case': '*PEAK*'}},
                                {'range': {
                                    'timestamp': {
                                        'gte': 'now-7d/d'
                                    }
                                }}
                            ]
                        }
                    },
                    'sort': [{'timestamp': {'order': 'desc'}}],
                    'size': 10
                }
            },
            'transaction_volume': {
                'regex': r'(?:show|display|get).*(?:transaction|txn).*volume.*(?:last|past)\s+(\d+)\s+day',
                'prod_query': {
                    'query': {
                        'range': {
                            'timestamp': {
                                'gte': 'now-{days}d/d'
                            }
                        }
                    },
                    'aggs': {
                        'daily_stats': {
                            'date_histogram': {
                                'field': 'timestamp',
                                'calendar_interval': 'day'
                            },
                            'aggs': {
                                'total_txns': {'value_count': {'field': 'txn_id'}},
                                'successful': {
                                    'filter': {'term': {'status': 'SUCCESS'}}
                                },
                                'failed': {
                                    'filter': {'term': {'status': 'FAILED'}}
                                },
                                'avg_amount': {'avg': {'field': 'amount'}}
                            }
                        }
                    },
                    'size': 0
                },
                'pte_query': {
                    'query': {
                        'range': {
                            'timestamp': {
                                'gte': 'now-{days}d/d'
                            }
                        }
                    },
                    'aggs': {
                        'daily_metrics': {
                            'date_histogram': {
                                'field': 'timestamp',
                                'calendar_interval': 'day'
                            },
                            'aggs': {
                                'avg_throughput': {'avg': {'field': 'throughput'}},
                                'avg_response_time': {'avg': {'field': 'response_time'}},
                                'avg_success_rate': {'avg': {'field': 'success_rate'}}
                            }
                        }
                    },
                    'size': 0
                }
            },
            'compare_pte_prod': {
                'regex': r'compar.*(?:pte|test).*(?:prod|production).*(?:batch|process)',
                'prod_query': {
                    'query': {
                        'bool': {
                            'must': [
                                {'term': {'txn_type': 'BATCH'}},
                                {'range': {
                                    'timestamp': {
                                        'gte': 'now-7d/d'
                                    }
                                }}
                            ]
                        }
                    },
                    'aggs': {
                        'total_txns': {'value_count': {'field': 'txn_id'}},
                        'success_rate': {
                            'avg': {
                                'script': "doc['status'].value == 'SUCCESS' ? 100 : 0"
                            }
                        },
                        'avg_response_time': {'avg': {'field': 'response_time_ms'}}
                    },
                    'size': 0
                },
                'pte_query': {
                    'query': {
                        'bool': {
                            'must': [
                                {'wildcard': {'metric_name': '*BATCH*'}},
                                {'range': {
                                    'timestamp': {
                                        'gte': 'now-7d/d'
                                    }
                                }}
                            ]
                        }
                    },
                    'aggs': {
                        'by_metric': {
                            'terms': {'field': 'metric_name.keyword'},
                            'aggs': {
                                'prod_avg': {'avg': {'field': 'prod_value'}},
                                'pte_avg': {'avg': {'field': 'pte_value'}},
                                'avg_variance': {'avg': {'field': 'variance'}}
                            }
                        }
                    },
                    'size': 0
                }
            },
            'success_rate_branch': {
                'regex': r'(?:what|show).*success rate.*branch\s+(\d+).*(?:yesterday|last day)',
                'prod_query': {
                    'query': {
                        'bool': {
                            'must': [
                                {'term': {'branch_id': '{branch_id}'}},
                                {'range': {
                                    'timestamp': {
                                        'gte': 'now-1d/d',
                                        'lt': 'now/d'
                                    }
                                }}
                            ]
                        }
                    },
                    'aggs': {
                        'total_txns': {'value_count': {'field': 'txn_id'}},
                        'successful': {
                            'filter': {'term': {'status': 'SUCCESS'}}
                        },
                        'avg_amount': {'avg': {'field': 'amount'}}
                    },
                    'size': 0
                },
                'pte_query': {
                    'query': {
                        'wildcard': {'test_case': '*BR_{branch_id}*'}
                    },
                    'sort': [{'timestamp': {'order': 'desc'}}],
                    'size': 5
                }
            },
            'failed_transactions': {
                'regex': r'(?:show|get|display).*failed.*transaction.*(?:error code|last hour)',
                'prod_query': {
                    'query': {
                        'bool': {
                            'must': [
                                {'term': {'status': 'FAILED'}},
                                {'range': {
                                    'timestamp': {
                                        'gte': 'now-1h'
                                    }
                                }}
                            ]
                        }
                    },
                    'aggs': {
                        'by_error_code': {
                            'terms': {
                                'field': 'error_code.keyword',
                                'size': 20
                            },
                            'aggs': {
                                'first_occurrence': {'min': {'field': 'timestamp'}},
                                'last_occurrence': {'max': {'field': 'timestamp'}},
                                'affected_types': {
                                    'terms': {'field': 'txn_type.keyword'}
                                }
                            }
                        }
                    },
                    'size': 0
                },
                'pte_query': {
                    'query': {
                        'bool': {
                            'should': [
                                {'wildcard': {'test_case': '*FAIL*'}},
                                {'wildcard': {'test_case': '*ERROR*'}}
                            ],
                            'minimum_should_match': 1
                        }
                    },
                    'sort': [{'timestamp': {'order': 'desc'}}],
                    'size': 10
                }
            }
        }
    
    def parse_query(self, query):
        """Parse natural language query and extract parameters"""
        query_lower = query.lower()
        
        for pattern_name, pattern_data in self.patterns.items():
            match = re.search(pattern_data['regex'], query_lower, re.IGNORECASE)
            if match:
                params = {}
                groups = match.groups()
                
                # Extract parameters based on pattern
                if 'branch' in pattern_name and groups:
                    params['branch_id'] = groups[0]
                elif 'volume' in pattern_name and groups:
                    params['days'] = groups[0]
                
                # Replace parameters in queries
                import json
                prod_query = json.dumps(pattern_data['prod_query'])
                pte_query = json.dumps(pattern_data['pte_query'])
                
                for key, value in params.items():
                    prod_query = prod_query.replace('{' + key + '}', str(value))
                    pte_query = pte_query.replace('{' + key + '}', str(value))
                
                return {
                    'pattern': pattern_name,
                    'prod_query': json.loads(prod_query),
                    'pte_query': json.loads(pte_query),
                    'params': params
                }
        
        return None

class ElasticsearchExecutor:
    """Execute queries on Elasticsearch"""
    
    def __init__(self, config):
        # Initialize Elasticsearch client
        self.es = Elasticsearch(**config)
        
    def execute_query(self, query, index):
        """Execute a query and return formatted results"""
        try:
            # Execute search
            response = self.es.search(index=index, body=query)
            
            # Format results based on response structure
            if 'aggregations' in response:
                # Process aggregation results
                return self._format_aggregations(response)
            else:
                # Process document hits
                return self._format_hits(response)
                
        except Exception as error:
            return {
                'error': str(error),
                'columns': [],
                'rows': [],
                'row_count': 0
            }
    
    def _format_aggregations(self, response):
        """Format aggregation results into table format"""
        aggs = response['aggregations']
        columns = []
        rows = []
        
        # Handle different aggregation structures
        for agg_name, agg_data in aggs.items():
            if 'buckets' in agg_data:
                # Terms or date_histogram aggregation
                for bucket in agg_data['buckets']:
                    row = {}
                    row['key'] = bucket.get('key_as_string', bucket['key'])
                    row['doc_count'] = bucket['doc_count']
                    
                    # Add sub-aggregations
                    for sub_agg_name, sub_agg_data in bucket.items():
                        if sub_agg_name not in ['key', 'doc_count', 'key_as_string']:
                            if isinstance(sub_agg_data, dict) and 'value' in sub_agg_data:
                                row[sub_agg_name] = round(sub_agg_data['value'], 2)
                            elif isinstance(sub_agg_data, dict) and 'doc_count' in sub_agg_data:
                                row[sub_agg_name] = sub_agg_data['doc_count']
                    
                    rows.append(row)
                
                if rows:
                    columns = list(rows[0].keys())
            else:
                # Metric aggregations
                row = {}
                for metric_name, metric_data in aggs.items():
                    if isinstance(metric_data, dict) and 'value' in metric_data:
                        row[metric_name] = round(metric_data['value'], 2) if metric_data['value'] else 0
                    elif isinstance(metric_data, dict) and 'doc_count' in metric_data:
                        row[metric_name] = metric_data['doc_count']
                
                if row:
                    columns = list(row.keys())
                    rows = [row]
        
        return {
            'columns': columns,
            'rows': rows,
            'row_count': len(rows)
        }
    
    def _format_hits(self, response):
        """Format document hits into table format"""
        hits = response['hits']['hits']
        
        if not hits:
            return {
                'columns': [],
                'rows': [],
                'row_count': 0
            }
        
        # Extract all unique fields from hits
        columns = set()
        rows = []
        
        for hit in hits:
            source = hit['_source']
            columns.update(source.keys())
            rows.append(source)
        
        columns = sorted(list(columns))
        
        return {
            'columns': columns,
            'rows': rows,
            'row_count': len(rows)
        }

# Initialize processor and executor
query_processor = NLQueryProcessor()
es_executor = ElasticsearchExecutor(ES_CONFIG)

@app.route('/')
def index():
    """Render the main interface"""
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process natural language query and return results"""
    data = request.json
    nl_query = data.get('query', '')
    
    if not nl_query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Parse the natural language query
    parsed = query_processor.parse_query(nl_query)
    
    if not parsed:
        return jsonify({
            'error': 'Could not understand the query. Please try rephrasing or use one of the sample queries.'
        }), 400
    
    # Execute queries on both indices
    prod_results = es_executor.execute_query(parsed['prod_query'], PROD_INDEX)
    pte_results = es_executor.execute_query(parsed['pte_query'], PTE_INDEX)
    
    import json
    return jsonify({
        'pattern': parsed['pattern'],
        'prod_query': json.dumps(parsed['prod_query'], indent=2),
        'pte_query': json.dumps(parsed['pte_query'], indent=2),
        'prod_results': prod_results,
        'pte_results': pte_results,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/sample-queries', methods=['GET'])
def get_sample_queries():
    """Return sample queries"""
    samples = [
        "How many payments initiated for branch 600 at peak hour?",
        "Show transaction volume for last 7 days",
        "Compare PTE metrics with production for batch processing",
        "What is the success rate for branch 450 yesterday?",
        "Show failed transactions by error code in the last hour"
    ]
    return jsonify({'samples': samples})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check Elasticsearch connection"""
    try:
        info = es_executor.es.info()
        return jsonify({
            'status': 'connected',
            'cluster_name': info['cluster_name'],
            'version': info['version']['number']
        })
    except Exception as e:
        return jsonify({
            'status': 'disconnected',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Natural Language Query Interface Server (Elasticsearch)")
    print("=" * 60)
    print("\nStarting server on http://localhost:5000")
    print("\nConfiguration:")
    print(f"  - Elasticsearch: {ES_CONFIG['hosts']}")
    print(f"  - Production Index: {PROD_INDEX}")
    print(f"  - PTE Index: {PTE_INDEX}")
    print("\nMake sure Elasticsearch is running and accessible!")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    