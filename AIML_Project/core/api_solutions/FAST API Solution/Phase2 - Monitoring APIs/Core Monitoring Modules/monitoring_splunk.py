"""
Splunk Monitoring Handler
Handles start/stop of Splunk monitoring and log fetching
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
import json
import xml.etree.ElementTree as ET
from config import Settings

logger = logging.getLogger(__name__)


class SplunkConfig:
    """Splunk configuration"""
    
    def __init__(self, settings: Settings):
        self.splunk_url = settings.SPLUNK_URL
        self.username = settings.SPLUNK_USERNAME
        self.password = settings.SPLUNK_PASSWORD
        self.index = settings.SPLUNK_INDEX
        self.timeout = settings.SPLUNK_TIMEOUT
        
        # API endpoints
        self.api_base = f"{self.splunk_url}/services"
        self.search_endpoint = f"{self.api_base}/search/jobs"


class SplunkMonitor:
    """Splunk monitoring operations"""
    
    def __init__(self, config: SplunkConfig):
        self.config = config
        self.session = requests.Session()
        self.session.auth = (self.config.username, self.config.password)
        self.session.verify = False  # For self-signed certificates
        
        self.monitoring_active = False
        self.last_fetch_time = None
        self.monitoring_config = {}
        self.active_searches = []
        
    def start_monitoring(
        self,
        index: Optional[str] = None,
        sourcetype: Optional[str] = None,
        search_query: Optional[str] = None,
        time_range_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Start Splunk monitoring
        
        Args:
            index: Splunk index to monitor
            sourcetype: Filter by sourcetype
            search_query: Custom SPL query
            time_range_minutes: Monitoring duration
            
        Returns:
            Status and configuration
        """
        try:
            idx = index or self.config.index
            
            logger.info(f"Starting Splunk monitoring for index: {idx}")
            
            # Verify index exists
            index_info = self._verify_index(idx)
            
            if not index_info:
                logger.warning(f"Index '{idx}' verification failed, proceeding anyway")
            
            # Build search query
            if search_query:
                base_query = search_query
            else:
                base_query = f"search index={idx}"
                if sourcetype:
                    base_query += f" sourcetype={sourcetype}"
            
            # Get initial event count
            event_count = self._get_event_count(base_query, time_range_minutes)
            
            # Store monitoring configuration
            self.monitoring_config = {
                "index": idx,
                "sourcetype": sourcetype,
                "search_query": base_query,
                "time_range_minutes": time_range_minutes,
                "start_time": datetime.now()
            }
            
            self.monitoring_active = True
            self.last_fetch_time = datetime.now()
            
            result = {
                "status": "started",
                "index": idx,
                "sourcetype": sourcetype,
                "search_query": base_query,
                "time_range_minutes": time_range_minutes,
                "start_time": self.last_fetch_time.isoformat(),
                "end_time": (self.last_fetch_time + timedelta(minutes=time_range_minutes)).isoformat(),
                "initial_event_count": event_count,
                "index_info": index_info,
                "monitoring_active": self.monitoring_active
            }
            
            logger.info(f"Splunk monitoring started successfully for {idx}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to start Splunk monitoring: {e}")
            raise Exception(f"Splunk monitoring start failed: {e}")
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """
        Stop Splunk monitoring
        
        Returns:
            Final status and summary
        """
        try:
            logger.info("Stopping Splunk monitoring")
            
            if not self.monitoring_active:
                return {
                    "status": "not_active",
                    "message": "Monitoring was not active"
                }
            
            # Get final event count
            final_count = None
            if self.monitoring_config:
                final_count = self._get_event_count(
                    self.monitoring_config.get("search_query"),
                    self.monitoring_config.get("time_range_minutes")
                )
            
            # Cancel any active searches
            for search_id in self.active_searches:
                self._cancel_search(search_id)
            
            duration = None
            if self.monitoring_config.get("start_time"):
                duration = (datetime.now() - self.monitoring_config["start_time"]).total_seconds() / 60
            
            self.monitoring_active = False
            self.active_searches = []
            
            result = {
                "status": "stopped",
                "stop_time": datetime.now().isoformat(),
                "duration_minutes": round(duration, 2) if duration else None,
                "final_event_count": final_count,
                "monitoring_active": self.monitoring_active
            }
            
            logger.info("Splunk monitoring stopped successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to stop Splunk monitoring: {e}")
            raise Exception(f"Splunk monitoring stop failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "monitoring_active": self.monitoring_active,
            "last_fetch_time": self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            "splunk_url": self.config.splunk_url,
            "index": self.monitoring_config.get("index") if self.monitoring_config else self.config.index,
            "active_searches": len(self.active_searches),
            "config": self.monitoring_config if self.monitoring_active else None
        }
    
    def search_events(
        self,
        search_query: str,
        earliest_time: str = "-15m",
        latest_time: str = "now",
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Execute Splunk search and return events
        
        Args:
            search_query: SPL search query
            earliest_time: Earliest time (Splunk format)
            latest_time: Latest time (Splunk format)
            max_results: Maximum number of results
            
        Returns:
            Search results
        """
        try:
            logger.info(f"Executing Splunk search: {search_query}")
            
            # Create search job
            search_data = {
                "search": search_query,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "output_mode": "json"
            }
            
            response = self.session.post(
                self.config.search_endpoint,
                data=search_data,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            
            # Get search ID from response
            search_id = self._extract_search_id(response.text)
            
            if not search_id:
                raise Exception("Failed to create search job")
            
            self.active_searches.append(search_id)
            
            # Wait for search to complete
            search_status = self._wait_for_search(search_id)
            
            # Get results
            results = self._get_search_results(search_id, max_results)
            
            # Clean up
            self._cancel_search(search_id)
            if search_id in self.active_searches:
                self.active_searches.remove(search_id)
            
            return {
                "status": "success",
                "search_query": search_query,
                "search_id": search_id,
                "event_count": results.get("result_count", 0),
                "events": results.get("results", []),
                "search_status": search_status,
                "fetched_at": datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to execute Splunk search: {e}")
            raise Exception(f"Splunk search failed: {e}")
    
    def search_errors(
        self,
        index: Optional[str] = None,
        time_range_minutes: int = 60,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Search for error events
        
        Args:
            index: Splunk index
            time_range_minutes: Time range
            max_results: Maximum results
            
        Returns:
            Error events
        """
        idx = index or self.config.index
        
        search_query = f'search index={idx} (level=ERROR OR level=error OR log_level=ERROR OR severity=ERROR)'
        earliest_time = f"-{time_range_minutes}m"
        
        return self.search_events(
            search_query=search_query,
            earliest_time=earliest_time,
            latest_time="now",
            max_results=max_results
        )
    
    def get_event_statistics(
        self,
        index: Optional[str] = None,
        time_range_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get event statistics using stats command
        
        Args:
            index: Splunk index
            time_range_minutes: Time range
            
        Returns:
            Statistics
        """
        try:
            idx = index or self.config.index
            
            # Search with stats aggregation
            search_query = f'''search index={idx} 
                | stats count by sourcetype, host
                | sort -count'''
            
            earliest_time = f"-{time_range_minutes}m"
            
            result = self.search_events(
                search_query=search_query,
                earliest_time=earliest_time,
                latest_time="now",
                max_results=1000
            )
            
            # Parse statistics
            stats = {
                "by_sourcetype": {},
                "by_host": {},
                "total_events": 0
            }
            
            for event in result.get("events", []):
                sourcetype = event.get("sourcetype", "unknown")
                host = event.get("host", "unknown")
                count = int(event.get("count", 0))
                
                stats["by_sourcetype"][sourcetype] = stats["by_sourcetype"].get(sourcetype, 0) + count
                stats["by_host"][host] = stats["by_host"].get(host, 0) + count
                stats["total_events"] += count
            
            return {
                "status": "success",
                "index": idx,
                "time_range_minutes": time_range_minutes,
                "statistics": stats,
                "fetched_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get event statistics: {e}")
            raise Exception(f"Event statistics fetch failed: {e}")
    
    def _verify_index(self, index: str) -> Optional[Dict]:
        """Verify index exists"""
        try:
            url = f"{self.config.api_base}/data/indexes/{index}"
            
            response = self.session.get(
                url,
                params={"output_mode": "json"},
                timeout=self.config.timeout
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "exists": True,
                "index_name": index,
                "response": "verified"
            }
            
        except Exception as e:
            logger.warning(f"Failed to verify index: {e}")
            return None
    
    def _get_event_count(self, search_query: str, time_range_minutes: int) -> int:
        """Get count of events"""
        try:
            count_query = f"{search_query} | stats count"
            earliest_time = f"-{time_range_minutes}m"
            
            result = self.search_events(
                search_query=count_query,
                earliest_time=earliest_time,
                latest_time="now",
                max_results=1
            )
            
            events = result.get("events", [])
            if events and len(events) > 0:
                return int(events[0].get("count", 0))
            
            return 0
            
        except Exception as e:
            logger.warning(f"Failed to get event count: {e}")
            return 0
    
    def _extract_search_id(self, response_text: str) -> Optional[str]:
        """Extract search ID from XML response"""
        try:
            root = ET.fromstring(response_text)
            sid_element = root.find(".//{http://dev.splunk.com/ns/rest}sid")
            
            if sid_element is not None:
                return sid_element.text
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract search ID: {e}")
            return None
    
    def _wait_for_search(self, search_id: str, max_wait_seconds: int = 60) -> Dict[str, Any]:
        """Wait for search to complete"""
        import time
        
        url = f"{self.config.search_endpoint}/{search_id}"
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = self.session.get(
                    url,
                    params={"output_mode": "json"},
                    timeout=self.config.timeout
                )
                
                response.raise_for_status()
                data = response.json()
                
                entry = data.get("entry", [{}])[0]
                content = entry.get("content", {})
                
                is_done = content.get("isDone", False)
                
                if is_done:
                    return {
                        "done": True,
                        "result_count": content.get("resultCount", 0),
                        "event_count": content.get("eventCount", 0)
                    }
                
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error checking search status: {e}")
                time.sleep(1)
        
        return {"done": False, "timeout": True}
    
    def _get_search_results(self, search_id: str, max_results: int) -> Dict[str, Any]:
        """Get search results"""
        try:
            url = f"{self.config.search_endpoint}/{search_id}/results"
            
            response = self.session.get(
                url,
                params={"output_mode": "json", "count": max_results},
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "result_count": len(data.get("results", [])),
                "results": data.get("results", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get search results: {e}")
            return {"result_count": 0, "results": []}
    
    def _cancel_search(self, search_id: str):
        """Cancel a search job"""
        try:
            url = f"{self.config.search_endpoint}/{search_id}/control"
            
            self.session.post(
                url,
                data={"action": "cancel"},
                timeout=self.config.timeout
            )
            
            logger.info(f"Cancelled search job: {search_id}")
            
        except Exception as e:
            logger.warning(f"Failed to cancel search {search_id}: {e}")
    
    def close(self):
        """Close session and cleanup"""
        # Cancel all active searches
        for search_id in self.active_searches:
            self._cancel_search(search_id)
        
        if self.session:
            self.session.close()