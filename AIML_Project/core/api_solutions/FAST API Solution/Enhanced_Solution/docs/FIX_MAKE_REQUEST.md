# 🔧 Fix: _make_request Method Signature Issue

## Problem:
The new code calls `_make_request(f"/applications")` but the old method expects a full URL.

## Solution:

---

## OPTION 1: Keep Endpoint Paths (Recommended)

Update `_make_request` to accept endpoint paths and build the full URL internally.

### In `monitoring/appd/client.py`:

```python
def _make_request(
    self, 
    endpoint: str,
    method: str = "GET",
    params: dict = None,
    data: dict = None
) -> Optional[dict]:
    """
    Make HTTP request to AppDynamics API
    
    Args:
        endpoint: API endpoint path (e.g., "/applications" or "/applications/123/tiers")
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body data
        
    Returns:
        Response data (dict or list) or None on error
    """
    try:
        # Build full URL
        # Remove leading slash if present to avoid double slashes
        endpoint = endpoint.lstrip('/')
        url = f"{self.config.APPD_BASE_URL}/controller/rest/{endpoint}"
        
        # Prepare request parameters
        request_params = {
            'output': 'JSON'
        }
        if params:
            request_params.update(params)
        
        # Make request
        if method.upper() == "GET":
            response = requests.get(
                url,
                params=request_params,
                auth=(self.config.APPD_USERNAME, self.config.APPD_PASSWORD),
                timeout=self.config.APPD_TIMEOUT_SECONDS,
                verify=self.config.APPD_VERIFY_SSL
            )
        elif method.upper() == "POST":
            response = requests.post(
                url,
                params=request_params,
                json=data,
                auth=(self.config.APPD_USERNAME, self.config.APPD_PASSWORD),
                timeout=self.config.APPD_TIMEOUT_SECONDS,
                verify=self.config.APPD_VERIFY_SSL
            )
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None
        
        # Check response status
        response.raise_for_status()
        
        # Parse JSON response
        return response.json()
        
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout for endpoint: {endpoint}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error for endpoint: {endpoint}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {response.status_code} for {endpoint}: {e}")
        return None
    except ValueError as e:
        logger.error(f"Invalid JSON response from {endpoint}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {endpoint}: {e}", exc_info=True)
        return None
```

---

## OPTION 2: Use Full URLs (Alternative)

If you prefer to pass full URLs, update all the method calls:

### In `monitoring/appd/client.py`:

```python
def _make_request(
    self, 
    url: str,
    method: str = "GET",
    params: dict = None,
    data: dict = None
) -> Optional[dict]:
    """Make HTTP request to AppDynamics API"""
    try:
        request_params = {'output': 'JSON'}
        if params:
            request_params.update(params)
        
        if method.upper() == "GET":
            response = requests.get(
                url,
                params=request_params,
                auth=(self.config.APPD_USERNAME, self.config.APPD_PASSWORD),
                timeout=self.config.APPD_TIMEOUT_SECONDS,
                verify=self.config.APPD_VERIFY_SSL
            )
        elif method.upper() == "POST":
            response = requests.post(
                url,
                params=request_params,
                json=data,
                auth=(self.config.APPD_USERNAME, self.config.APPD_PASSWORD),
                timeout=self.config.APPD_TIMEOUT_SECONDS,
                verify=self.config.APPD_VERIFY_SSL
            )
        else:
            logger.error(f"Unsupported method: {method}")
            return None
        
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return None


def get_application(self, application_name: str) -> Optional[dict]:
    """Get application by name"""
    # Build full URL
    url = f"{self.config.APPD_BASE_URL}/controller/rest/applications"
    response = self._make_request(url)
    
    if isinstance(response, list):
        for app in response:
            if app.get('name') == application_name:
                return app
        return None
    
    return response


def get_tiers(self, application_name: str) -> List[dict]:
    """Get all tiers for application"""
    # Build full URL
    url = f"{self.config.APPD_BASE_URL}/controller/rest/applications/{application_name}/tiers"
    response = self._make_request(url)
    
    if response is None:
        return []
    elif isinstance(response, list):
        return response
    elif isinstance(response, dict):
        return [response]
    return []


def get_nodes(self, application_name: str, tier_name: str) -> List[dict]:
    """Get all nodes for tier"""
    # Build full URL
    url = f"{self.config.APPD_BASE_URL}/controller/rest/applications/{application_name}/tiers/{tier_name}/nodes"
    response = self._make_request(url)
    
    if response is None:
        return []
    elif isinstance(response, list):
        return response
    elif isinstance(response, dict):
        return [response]
    return []
```

---

## 🎯 RECOMMENDED: Use Option 1 (Endpoint Paths)

This is cleaner and avoids repeating the base URL everywhere.

### Complete client.py with Option 1:

```python
"""
AppDynamics REST API Client
Handles all HTTP communication with AppDynamics Controller
"""
import requests
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AppDynamicsClient:
    """Client for AppDynamics REST API"""
    
    def __init__(self, config):
        """
        Initialize AppDynamics client
        
        Args:
            config: Configuration object with AppD settings
        """
        self.config = config
        self.base_url = config.APPD_BASE_URL.rstrip('/')
        self.controller_url = f"{self.base_url}/controller/rest"
    
    def _make_request(
        self, 
        endpoint: str,
        method: str = "GET",
        params: dict = None,
        data: dict = None
    ) -> Optional[Any]:
        """
        Make HTTP request to AppDynamics API
        
        Args:
            endpoint: API endpoint path (e.g., "applications" or "applications/123/tiers")
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data (dict or list) or None on error
        """
        try:
            # Build full URL
            endpoint = endpoint.lstrip('/')
            url = f"{self.controller_url}/{endpoint}"
            
            # Prepare request parameters
            request_params = {'output': 'JSON'}
            if params:
                request_params.update(params)
            
            logger.debug(f"AppD API Request: {method} {url}")
            
            # Make request
            if method.upper() == "GET":
                response = requests.get(
                    url,
                    params=request_params,
                    auth=(self.config.APPD_USERNAME, self.config.APPD_PASSWORD),
                    timeout=self.config.APPD_TIMEOUT_SECONDS,
                    verify=self.config.APPD_VERIFY_SSL
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url,
                    params=request_params,
                    json=data,
                    auth=(self.config.APPD_USERNAME, self.config.APPD_PASSWORD),
                    timeout=self.config.APPD_TIMEOUT_SECONDS,
                    verify=self.config.APPD_VERIFY_SSL
                )
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Check response status
            response.raise_for_status()
            
            # Parse JSON response
            result = response.json()
            logger.debug(f"AppD API Response: {type(result)} with {len(result) if isinstance(result, list) else 'N/A'} items")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for endpoint: {endpoint}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for endpoint: {endpoint}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {response.status_code} for {endpoint}: {e}")
            return None
        except ValueError as e:
            logger.error(f"Invalid JSON response from {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {e}", exc_info=True)
            return None
    
    
    def get_application(self, application_name: str) -> Optional[dict]:
        """
        Get application by name from AppDynamics
        
        Args:
            application_name: Name of the application
            
        Returns:
            Application dict or None if not found
        """
        try:
            # Get all applications
            response = self._make_request("applications")
            
            if not response:
                return None
            
            # Response is a list of applications
            if isinstance(response, list):
                # Find the application by name (case-insensitive)
                for app in response:
                    if app.get('name', '').lower() == application_name.lower():
                        logger.info(f"Found application: {app.get('name')} (ID: {app.get('id')})")
                        return app
                
                logger.warning(f"Application '{application_name}' not found in AppD")
                logger.debug(f"Available applications: {[a.get('name') for a in response]}")
                return None
            
            # If response is a dict (single app), return it
            elif isinstance(response, dict):
                return response
            
            else:
                logger.error(f"Unexpected response type: {type(response)}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get application {application_name}: {e}")
            return None
    
    
    def get_tiers(self, application_name: str) -> List[dict]:
        """
        Get all tiers for an application
        
        Args:
            application_name: Name of the application
            
        Returns:
            List of tier dicts
        """
        try:
            response = self._make_request(f"applications/{application_name}/tiers")
            
            # Ensure response is a list
            if response is None:
                return []
            elif isinstance(response, list):
                logger.info(f"Found {len(response)} tiers for {application_name}")
                return response
            elif isinstance(response, dict):
                return [response]  # Wrap single tier in list
            else:
                logger.error(f"Unexpected tiers response type: {type(response)}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get tiers for {application_name}: {e}")
            return []
    
    
    def get_nodes(self, application_name: str, tier_name: str) -> List[dict]:
        """
        Get all nodes for a tier
        
        Args:
            application_name: Name of the application
            tier_name: Name of the tier
            
        Returns:
            List of node dicts
        """
        try:
            response = self._make_request(
                f"applications/{application_name}/tiers/{tier_name}/nodes"
            )
            
            # Ensure response is a list
            if response is None:
                return []
            elif isinstance(response, list):
                logger.info(f"Found {len(response)} nodes for tier {tier_name}")
                return response
            elif isinstance(response, dict):
                return [response]  # Wrap single node in list
            else:
                logger.error(f"Unexpected nodes response type: {type(response)}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get nodes for {tier_name}: {e}")
            return []
    
    
    def get_node_cpm(self, application_name: str, node_id: int) -> float:
        """
        Get Calls Per Minute metric for a node
        
        Args:
            application_name: Name of the application
            node_id: Node ID
            
        Returns:
            float: CPM value, or 0.0 if not available
        """
        try:
            # Get metric data for last 5 minutes
            response = self._make_request(
                f"applications/{application_name}/metric-data",
                params={
                    "metric-path": f"Application Infrastructure Performance|{node_id}|Agent|Calls per Minute",
                    "time-range-type": "BEFORE_NOW",
                    "duration-in-mins": 5,
                    "rollup": "false"
                }
            )
            
            if not response:
                return 0.0
            
            # Parse metric data
            if isinstance(response, list) and len(response) > 0:
                metric = response[0]
                values = metric.get('metricValues', [])
                if values and len(values) > 0:
                    # Get most recent value
                    cpm = float(values[-1].get('value', 0))
                    logger.debug(f"Node {node_id} CPM: {cpm:.2f}")
                    return cpm
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Failed to get CPM for node {node_id}: {e}")
            return 0.0
```

---

## 🧪 Testing

After updating, test the client:

```python
# Test in Python console or create a test script
from monitoring.appd.config import appd_config
from monitoring.appd.client import AppDynamicsClient

client = AppDynamicsClient(appd_config)

# Test get_application
app = client.get_application("icg-tts-paymentinitiation-pte-173720_PTE")
print(f"Found app: {app}")

# Test get_tiers
if app:
    tiers = client.get_tiers(app['name'])
    print(f"Found {len(tiers)} tiers")
    
    # Test get_nodes
    for tier in tiers:
        nodes = client.get_nodes(app['name'], tier['name'])
        print(f"Tier {tier['name']}: {len(nodes)} nodes")
```

---

## 📋 Summary

**Option 1 (Recommended):** Use endpoint paths like `"applications"` and build URL in `_make_request`
- ✅ Cleaner code
- ✅ Less repetition
- ✅ Easier to maintain

**Option 2:** Use full URLs everywhere
- ❌ More verbose
- ❌ Repeat base URL in every method
- ✅ More explicit

Apply **Option 1** for the best solution! 🚀