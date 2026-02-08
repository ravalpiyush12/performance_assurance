"""
Kibana Monitoring Handler
Handles start/stop of Kibana monitoring and log fetching
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
import json
from config import Settings

logger = logging.getLogger(__name__)


class KibanaConfig:
    """Kibana configuration"""
    
    def __init__(self, settings: Settings):
        self.kibana_url = settings.KIBANA_URL
        self.elasticsearch_url = settings.ELASTICSEARCH_URL
        self.username = settings.KIBANA_USERNAME
        self.password = settings.KIBANA_PASSWORD
        self.index_pattern = settings.KIBANA_INDEX_PATTERN
        self.timeout = settings.KIBANA_TIMEOUT
        
        # Build authentication
        self.auth = HTTPBasicAuth(self.username, self.password) if self.username else None
        
        # API base URLs
        self.kibana_api = f"{self.kibana_url}/api"
        self.es_api = f"{self.elasticsearch_url}"


class KibanaMonitor:
    """Kibana monitoring operations"""
    
    def __init__(self, config: KibanaConfig):
        self.config = config
        self.session = requests.Session()
        if self.config.auth:
            self.session.auth = self.config.auth
        
        # Kibana requires kbn-xsrf header
        self.session.headers.update({
            'kbn-xsrf': 'true',
            'Content-Type': 'application/json'
        })
        
        self.monitoring_active = False
        self.last_fetch_time = None
        self.monitoring_config = {}
        
    def start_monitoring(
        self,
        index_pattern: Optional[str] = None,
        time_range_minutes: int = 60,
        query: Optional[str] = None,
        log_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start Kibana monitoring
        
        Args:
            index_pattern: Elasticsearch index pattern
            time_range_minutes: Monitoring duration
            query: Optional query filter
            log_level: Filter by log level (ERROR, WARN, INFO, DEBUG)
            
        Returns:
            Status and configuration
        """
        try:
            index = index_pattern or self.config.index_pattern
            
            logger.info(f"Starting Kibana monitoring for index: {index}")
            
            # Verify index exists
            index_info = self._verify_index(index)
            
            if not index_info:
                raise Exception(f"Index pattern '{index}' not found or inaccessible")
            
            # Build monitoring configuration
            self.monitoring_config = {
                "index_pattern": index,
                "time_range_minutes": time_range_minutes,
                "query": query,
                "log_level": log_level,
                "start_time": datetime.now()
            }
            
            # Get initial log count
            log_count = self._get_log_count(index, time_range_minutes, query, log_level)
            
            self.monitoring_active = True
            self.last_fetch_time = datetime.now()
            
            result = {
                "status": "started",
                "index_pattern": index,
                "time_range_minutes": time_range_minutes,
                "query": query,
                "log_level": log_level,
                "start_time": self.last_fetch_time.isoformat(),
                "end_time": (self.last_fetch_time + timedelta(minutes=time_range_minutes)).isoformat(),
                "initial_log_count": log_count,
                "index_info": index_info,
                "monitoring_active": self.monitoring_active
            }
            
            logger.info(f"Kibana monitoring started successfully for {index}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to start Kibana monitoring: {e}")
            raise Exception(f"Kibana monitoring start failed: {e}")
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """
        Stop Kibana monitoring
        
        Returns:
            Final status and summary
        """
        try:
            logger.info("Stopping Kibana monitoring")
            
            if not self.monitoring_active:
                return {
                    "status": "not_active",
                    "message": "Monitoring was not active"
                }
            
            # Get final log count
            final_count = None
            if self.monitoring_config:
                final_count = self._get_log_count(
                    self.monitoring_config.get("index_pattern"),
                    self.monitoring_config.get("time_range_minutes"),
                    self.monitoring_config.get("query"),
                    self.monitoring_config.get("log_level")
                )
            
            duration = None
            if self.monitoring_config.get("start_time"):
                duration = (datetime.now() - self.monitoring_config["start_time"]).total_seconds() / 60
            
            self.monitoring_active = False
            
            result = {
                "status": "stopped",
                "stop_time": datetime.now().isoformat(),
                "duration_minutes": round(duration, 2) if duration else None,
                "final_log_count": final_count,
                "monitoring_active": self.monitoring_active
            }
            
            logger.info("Kibana monitoring stopped successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to stop Kibana monitoring: {e}")
            raise Exception(f"Kibana monitoring stop failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "monitoring_active": self.monitoring_active,
            "last_fetch_time": self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            "kibana_url": self.config.kibana_url,
            "index_pattern": self.monitoring_config.get("index_pattern") if self.monitoring_config else self.config.index_pattern,
            "config": self.monitoring_config if self.monitoring_active else None
        }
    
    def fetch_logs(
        self,
        index_pattern: Optional[str] = None,
        time_range_minutes: int = 15,
        size: int = 100,
        query: Optional[str] = None,
        log_level: Optional[str] = None,
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Fetch logs from Elasticsearch via Kibana
        
        Args:
            index_pattern: Index pattern
            time_range_minutes: Time range
            size: Number of logs to fetch
            query: Optional query string
            log_level: Filter by log level
            sort_order: Sort order (asc/desc)
            
        Returns:
            Logs data
        """
        try:
            index = index_pattern or self.config.index_pattern
            
            logger.info(f"Fetching logs from Kibana: {index}")
            
            # Build Elasticsearch query
            es_query = self._build_query(time_range_minutes, query, log_level)
            
            # Query Elasticsearch
            url = f"{self.config.es_api}/{index}/_search"
            
            body = {
                "query": es_query,
                "size": size,
                "sort": [
                    {"@timestamp": {"order": sort_order}}
                ]
            }
            
            response = self.session.post(
                url,
                json=body,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            
            data = response.json()
            hits = data.get("hits", {})
            
            # Extract log entries
            logs = []
            for hit in hits.get("hits", []):
                log_entry = hit.get("_source", {})
                log_entry["_id"] = hit.get("_id")
                log_entry["_index"] = hit.get("_index")
                logs.append(log_entry)
            
            return {
                "status": "success",
                "index_pattern": index,
                "time_range_minutes": time_range_minutes,
                "total_hits": hits.get("total", {}).get("value", 0),
                "returned_logs": len(logs),
                "logs": logs,
                "query_used": es_query,
                "fetched_at": datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Kibana logs: {e}")
            raise Exception(f"Kibana logs fetch failed: {e}")
    
    def search_errors(
        self,
        index_pattern: Optional[str] = None,
        time_range_minutes: int = 60,
        size: int = 50
    ) -> Dict[str, Any]:
        """
        Search for error logs
        
        Args:
            index_pattern: Index pattern
            time_range_minutes: Time range
            size: Number of errors to fetch
            
        Returns:
            Error logs
        """
        return self.fetch_logs(
            index_pattern=index_pattern,
            time_range_minutes=time_range_minutes,
            size=size,
            log_level="ERROR",
            sort_order="desc"
        )
    
    def get_log_statistics(
        self,
        index_pattern: Optional[str] = None,
        time_range_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get log statistics (aggregations by level)
        
        Args:
            index_pattern: Index pattern
            time_range_minutes: Time range
            
        Returns:
            Statistics
        """
        try:
            index = index_pattern or self.config.index_pattern
            
            # Build aggregation query
            url = f"{self.config.es_api}/{index}/_search"
            
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=time_range_minutes)
            
            body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": start_time.isoformat(),
                                        "lte": end_time.isoformat()
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": 0,
                "aggs": {
                    "log_levels": {
                        "terms": {
                            "field": "level.keyword",
                            "size": 10
                        }
                    },
                    "logs_over_time": {
                        "date_histogram": {
                            "field": "@timestamp",
                            "fixed_interval": "5m"
                        }
                    }
                }
            }
            
            response = self.session.post(
                url,
                json=body,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            aggregations = data.get("aggregations", {})
            
            # Parse log levels
            log_levels = {}
            for bucket in aggregations.get("log_levels", {}).get("buckets", []):
                log_levels[bucket["key"]] = bucket["doc_count"]
            
            # Parse timeline
            timeline = []
            for bucket in aggregations.get("logs_over_time", {}).get("buckets", []):
                timeline.append({
                    "timestamp": bucket["key_as_string"],
                    "count": bucket["doc_count"]
                })
            
            return {
                "status": "success",
                "index_pattern": index,
                "time_range_minutes": time_range_minutes,
                "total_logs": data.get("hits", {}).get("total", {}).get("value", 0),
                "log_levels": log_levels,
                "timeline": timeline,
                "fetched_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get log statistics: {e}")
            raise Exception(f"Log statistics fetch failed: {e}")
    
    def _verify_index(self, index_pattern: str) -> Optional[Dict]:
        """Verify index exists and is accessible"""
        try:
            url = f"{self.config.es_api}/{index_pattern}"
            
            response = self.session.get(url, timeout=self.config.timeout)
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            
            data = response.json()
            
            # Get index names
            indices = list(data.keys()) if isinstance(data, dict) else []
            
            return {
                "exists": True,
                "indices_count": len(indices),
                "indices": indices[:5]  # First 5 indices
            }
            
        except Exception as e:
            logger.error(f"Failed to verify index: {e}")
            return None
    
    def _get_log_count(
        self,
        index_pattern: str,
        time_range_minutes: int,
        query: Optional[str] = None,
        log_level: Optional[str] = None
    ) -> int:
        """Get count of logs matching criteria"""
        try:
            url = f"{self.config.es_api}/{index_pattern}/_count"
            
            es_query = self._build_query(time_range_minutes, query, log_level)
            
            body = {"query": es_query}
            
            response = self.session.post(url, json=body, timeout=self.config.timeout)
            response.raise_for_status()
            
            data = response.json()
            return data.get("count", 0)
            
        except Exception as e:
            logger.warning(f"Failed to get log count: {e}")
            return 0
    
    def _build_query(
        self,
        time_range_minutes: int,
        query: Optional[str] = None,
        log_level: Optional[str] = None
    ) -> Dict:
        """Build Elasticsearch query"""
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=time_range_minutes)
        
        must_clauses = [
            {
                "range": {
                    "@timestamp": {
                        "gte": start_time.isoformat(),
                        "lte": end_time.isoformat()
                    }
                }
            }
        ]
        
        # Add log level filter
        if log_level:
            must_clauses.append({
                "match": {
                    "level": log_level
                }
            })
        
        # Add custom query
        if query:
            must_clauses.append({
                "query_string": {
                    "query": query
                }
            })
        
        return {
            "bool": {
                "must": must_clauses
            }
        }
    
    def close(self):
        """Close session"""
        if self.session:
            self.session.close()