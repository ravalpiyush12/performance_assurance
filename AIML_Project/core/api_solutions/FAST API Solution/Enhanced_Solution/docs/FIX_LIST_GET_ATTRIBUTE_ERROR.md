# 🔧 Fix: 'list' has no attribute 'get' Error in Discovery

## Problem:
AppDynamics API returns a LIST of applications, not a single object.
When you call `app_data.get('id')`, it fails because app_data is a list.

## Root Cause:
```python
# This returns a LIST, not a dict:
app_data = self.client.get_application(application_name)
# app_data = [{...}]  ← List!

# Then you try:
app_id = app_data.get('id')  # ❌ Error: list has no attribute 'get'
```

---

## SOLUTION:

### FIX 1: Update AppDynamics Client (client.py)

In `monitoring/appd/client.py`, update the `get_application` method:

```python
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
        response = self._make_request(f"/applications")
        
        if not response:
            return None
        
        # Response is a list of applications
        if isinstance(response, list):
            # Find the application by name (case-insensitive)
            for app in response:
                if app.get('name', '').lower() == application_name.lower():
                    return app
            
            # Try exact match if case-insensitive didn't work
            for app in response:
                if app.get('name') == application_name:
                    return app
            
            logger.warning(f"Application '{application_name}' not found in AppD")
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
```

---

### FIX 2: Update Discovery Service (discovery.py)

In `monitoring/appd/discovery.py`, update the `discover_application` method to handle None:

```python
def discover_application(
    self,
    lob_id: int,
    lob_name: str,
    application_name: str
) -> dict:
    """
    Discover a single application
    
    Returns:
        dict with stats or None if app not found
    """
    logger.info(f"Discovering application: {application_name} for LOB: {lob_name}")
    
    tiers_count = 0
    nodes_count = 0
    active_nodes_count = 0
    
    try:
        # Get application from AppD
        app_data = self.client.get_application(application_name)
        
        # ✅ FIX: Check if app was found
        if not app_data:
            logger.error(f"Application not found in AppDynamics: {application_name}")
            return {
                'success': False,
                'error': f"Application '{application_name}' not found in AppDynamics",
                'tiers_count': 0,
                'nodes_count': 0,
                'active_nodes_count': 0
            }
        
        # ✅ FIX: Verify it's a dict, not a list
        if isinstance(app_data, list):
            if len(app_data) > 0:
                app_data = app_data[0]  # Take first item
            else:
                logger.error(f"Empty list returned for: {application_name}")
                return {
                    'success': False,
                    'error': 'Empty response from AppDynamics',
                    'tiers_count': 0,
                    'nodes_count': 0,
                    'active_nodes_count': 0
                }
        
        # Now app_data is guaranteed to be a dict
        app_id_appd = app_data.get('id')
        app_name = app_data.get('name', application_name)
        
        logger.info(f"Found application: {app_name} (ID: {app_id_appd})")
        
        # Save application to database
        app_id = self.db.upsert_application(lob_id, {
            'name': app_name,
            'id': app_id_appd,
            'total_tiers': 0,
            'total_nodes': 0,
            'active_nodes': 0,
            'inactive_nodes': 0
        })
        
        # Get all tiers for this application
        tiers = self.client.get_tiers(app_name)
        
        # ✅ FIX: Handle if tiers is None or not a list
        if not tiers:
            logger.warning(f"No tiers found for application: {app_name}")
            tiers = []
        elif not isinstance(tiers, list):
            logger.error(f"Unexpected tiers type: {type(tiers)}")
            tiers = []
        
        tiers_count = len(tiers)
        logger.info(f"Found {tiers_count} tiers for {app_name}")
        
        for tier in tiers:
            # ✅ FIX: Verify tier is a dict
            if not isinstance(tier, dict):
                logger.warning(f"Skipping invalid tier: {tier}")
                continue
            
            tier_name = tier.get('name')
            tier_id_appd = tier.get('id')
            
            if not tier_name:
                logger.warning(f"Tier missing name: {tier}")
                continue
            
            logger.info(f"Processing tier: {tier_name}")
            
            # Save tier
            tier_id = self.db.upsert_tier(app_id, {
                'name': tier_name,
                'id': tier_id_appd,
                'type': tier.get('type'),
                'total_nodes': 0,
                'active_nodes': 0
            })
            
            # Get all nodes for this tier
            nodes = self.client.get_nodes(app_name, tier_name)
            
            # ✅ FIX: Handle if nodes is None or not a list
            if not nodes:
                logger.warning(f"No nodes found for tier: {tier_name}")
                nodes = []
            elif not isinstance(nodes, list):
                logger.error(f"Unexpected nodes type: {type(nodes)}")
                nodes = []
            
            logger.info(f"Found {len(nodes)} nodes in tier: {tier_name}")
            
            for node in nodes:
                # ✅ FIX: Verify node is a dict
                if not isinstance(node, dict):
                    logger.warning(f"Skipping invalid node: {node}")
                    continue
                
                node_name = node.get('name')
                node_id_appd = node.get('id')
                
                if not node_name or not node_id_appd:
                    logger.warning(f"Node missing name/id: {node}")
                    continue
                
                try:
                    # Get CPM (Calls Per Minute) metric
                    cpm = self.client.get_node_cpm(app_name, node_id_appd)
                    
                    # ✅ FIX: Handle if cpm is None or invalid
                    if cpm is None:
                        logger.warning(f"Could not get CPM for node: {node_name}, defaulting to 0")
                        cpm = 0.0
                    
                    # Classify as active/inactive
                    is_active = cpm >= self.config.APPD_ACTIVE_NODE_THRESHOLD
                    
                    # Save node with CPM
                    self.db.upsert_node(tier_id, app_id, {
                        'name': node_name,
                        'id': node_id_appd,
                        'machine_name': node.get('machineName'),
                        'ip_address': node.get('ipAddresses', [None])[0] if node.get('ipAddresses') else None,
                        'calls_per_minute': cpm,
                        'threshold': self.config.APPD_ACTIVE_NODE_THRESHOLD,
                        'type': node.get('type'),
                        'agent_version': node.get('agentVersion')
                    })
                    
                    nodes_count += 1
                    if is_active:
                        active_nodes_count += 1
                    
                    logger.info(
                        f"Node {node_name}: CPM={cpm:.2f}, "
                        f"Active={'Yes' if is_active else 'No'}"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to process node {node_name}: {e}")
                    continue
        
        # Update application totals
        self.db.upsert_application(lob_id, {
            'name': app_name,
            'id': app_id_appd,
            'total_tiers': tiers_count,
            'total_nodes': nodes_count,
            'active_nodes': active_nodes_count,
            'inactive_nodes': nodes_count - active_nodes_count
        })
        
        logger.info(
            f"✅ Discovery complete for {app_name}: "
            f"{tiers_count} tiers, {nodes_count} nodes "
            f"({active_nodes_count} active, {nodes_count - active_nodes_count} inactive)"
        )
        
        return {
            'success': True,
            'tiers_count': tiers_count,
            'nodes_count': nodes_count,
            'active_nodes_count': active_nodes_count
        }
        
    except Exception as e:
        logger.error(f"Failed to discover {application_name}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'tiers_count': 0,
            'nodes_count': 0,
            'active_nodes_count': 0
        }
```

---

### FIX 3: Add Safe Get Helper (Optional but Recommended)

Add this helper function at the top of `discovery.py`:

```python
def safe_get(data, key, default=None):
    """
    Safely get value from data, handling lists and dicts
    """
    if isinstance(data, dict):
        return data.get(key, default)
    elif isinstance(data, list) and len(data) > 0:
        return data[0].get(key, default) if isinstance(data[0], dict) else default
    return default
```

Then use it like:
```python
app_id = safe_get(app_data, 'id')
app_name = safe_get(app_data, 'name', application_name)
```

---

### FIX 4: Update get_tiers and get_nodes in client.py

Make sure these methods also handle lists properly:

```python
def get_tiers(self, application_name: str) -> List[dict]:
    """Get all tiers for an application"""
    try:
        response = self._make_request(f"/applications/{application_name}/tiers")
        
        # Ensure response is a list
        if response is None:
            return []
        elif isinstance(response, list):
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
    """Get all nodes for a tier"""
    try:
        response = self._make_request(
            f"/applications/{application_name}/tiers/{tier_name}/nodes"
        )
        
        # Ensure response is a list
        if response is None:
            return []
        elif isinstance(response, list):
            return response
        elif isinstance(response, dict):
            return [response]  # Wrap single node in list
        else:
            logger.error(f"Unexpected nodes response type: {type(response)}")
            return []
            
    except Exception as e:
        logger.error(f"Failed to get nodes for {tier_name}: {e}")
        return []
```

---

### FIX 5: Update get_node_cpm to Return Float

```python
def get_node_cpm(self, application_name: str, node_id: int) -> float:
    """
    Get Calls Per Minute metric for a node
    
    Returns:
        float: CPM value, or 0.0 if not available
    """
    try:
        # Get metric data for last 5 minutes
        response = self._make_request(
            f"/applications/{application_name}/metric-data",
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
                return float(values[-1].get('value', 0))
        
        return 0.0
        
    except Exception as e:
        logger.error(f"Failed to get CPM for node {node_id}: {e}")
        return 0.0
```

---

## 🧪 Testing

After applying fixes, test with:

```bash
curl -X POST http://localhost:8000/api/v1/monitoring/appd/discovery/run \
  -H "Content-Type: application/json" \
  -d '{
    "config_name": "Digital_tech_CDV3_27Feb_1247",
    "lob_name": "Digital Technology",
    "applications": ["icg-tts-paymentinitiation-pte-173720_PTE"]
  }'
```

Watch the logs for:
```
[Discovery] Found application: icg-tts-paymentinitiation-pte-173720_PTE (ID: 123)
[Discovery] Found 3 tiers for icg-tts-paymentinitiation-pte-173720_PTE
[Discovery] Processing tier: Web-Tier
[Discovery] Found 5 nodes in tier: Web-Tier
[Discovery] Node WebNode1: CPM=150.25, Active=Yes
[Discovery] Node WebNode2: CPM=2.50, Active=No
...
[Discovery] ✅ Discovery complete for icg-tts-paymentinitiation-pte-173720_PTE: 3 tiers, 12 nodes (8 active, 4 inactive)
```

---

## 📋 Summary of Changes

| File | Method | Fix |
|------|--------|-----|
| `client.py` | `get_application()` | Search list for app by name |
| `client.py` | `get_tiers()` | Ensure returns list |
| `client.py` | `get_nodes()` | Ensure returns list |
| `client.py` | `get_node_cpm()` | Return 0.0 on error |
| `discovery.py` | `discover_application()` | Handle None, lists, validate all data |

---

## 🔑 Key Points

1. **AppD API returns lists** - Applications, tiers, nodes are all lists
2. **Always validate type** - Check `isinstance(data, dict)` before `.get()`
3. **Handle None gracefully** - API can return None on errors
4. **Default to safe values** - Use 0.0 for CPM, empty list for collections
5. **Log extensively** - Help debugging when things fail

Apply these fixes and your discovery should work! 🚀