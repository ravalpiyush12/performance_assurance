# 🔧 Fix: Discovery Endpoint 422 Unprocessable Entity Error

## Problem:
The DiscoveryRequest model doesn't match what the UI sends.

## Solution:

---

## STEP 1: Update DiscoveryRequest Model in routes.py

Replace the existing `DiscoveryRequest` class with this:

```python
# OLD (Wrong):
class DiscoveryRequest(BaseModel):
    lob_names: List[str]  # ❌ Expects list of LOB names

# NEW (Correct):
class DiscoveryRequest(BaseModel):
    """Request model for discovery - matches UI input"""
    config_name: str
    lob_name: str
    applications: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "config_name": "Retail_Q1_2026",
                "lob_name": "Retail",
                "applications": ["RetailWeb", "RetailAPI"]
            }
        }
```

---

## STEP 2: Update /discovery/run Endpoint

Replace the entire endpoint with this:

```python
@router.post("/discovery/run")
async def run_discovery(request: DiscoveryRequest, background_tasks: BackgroundTasks):
    """
    Run discovery for a config
    Creates background task to discover applications, tiers, and nodes
    """
    if not discovery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        # Get config from database to get LOB_ID
        config = appd_db.get_config_by_name(request.config_name)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Config '{request.config_name}' not found. Please save config first."
            )
        
        lob_id = config['lob_id']
        
        # Create discovery task
        task_id = str(uuid.uuid4())
        
        # Run discovery in background
        background_tasks.add_task(
            execute_discovery_task,
            task_id,
            lob_id,
            request.lob_name,
            request.applications
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "initiated",
            "config_name": request.config_name,
            "lob_name": request.lob_name,
            "applications": request.applications,
            "message": "Discovery started in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start discovery: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start discovery: {str(e)}"
        )
```

---

## STEP 3: Update Background Task Function

Replace the `execute_discovery_task` function:

```python
def execute_discovery_task(
    task_id: str, 
    lob_id: int,
    lob_name: str, 
    applications: List[str]
):
    """
    Background discovery task
    Discovers apps, tiers, nodes for the given applications
    """
    try:
        logger.info(f"[Discovery Task {task_id}] Starting for LOB: {lob_name}")
        
        # Create discovery log
        log_id = appd_db.create_discovery_log(lob_id)
        
        stats = {
            'applications': 0,
            'tiers': 0,
            'nodes': 0,
            'active_nodes': 0
        }
        
        # Discover each application
        for app_name in applications:
            try:
                logger.info(f"[Discovery Task {task_id}] Discovering: {app_name}")
                
                # Run discovery for this application
                app_result = discovery_service.discover_application(
                    lob_id=lob_id,
                    lob_name=lob_name,
                    application_name=app_name
                )
                
                if app_result:
                    stats['applications'] += 1
                    stats['tiers'] += app_result.get('tiers_count', 0)
                    stats['nodes'] += app_result.get('nodes_count', 0)
                    stats['active_nodes'] += app_result.get('active_nodes_count', 0)
                
            except Exception as e:
                logger.error(f"[Discovery Task {task_id}] Failed for {app_name}: {e}")
        
        # Update discovery log with results
        appd_db.complete_discovery_log(log_id, stats, status='SUCCESS')
        
        # Update last discovery run timestamp
        appd_db.update_lob_discovery_time(lob_id)
        
        logger.info(f"[Discovery Task {task_id}] Completed: {stats}")
        
        return {
            'task_id': task_id,
            'status': 'SUCCESS',
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"[Discovery Task {task_id}] Failed: {e}", exc_info=True)
        try:
            appd_db.complete_discovery_log(
                log_id, 
                stats, 
                status='FAILED',
                error=str(e)
            )
        except:
            pass
        
        return {
            'task_id': task_id,
            'status': 'FAILED',
            'error': str(e)
        }
```

---

## STEP 4: Add Helper Method to Discovery Service

In `monitoring/appd/discovery.py`, add this method if it doesn't exist:

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
        dict with stats: {
            'tiers_count': int,
            'nodes_count': int,
            'active_nodes_count': int
        }
    """
    logger.info(f"Discovering application: {application_name} for LOB: {lob_name}")
    
    tiers_count = 0
    nodes_count = 0
    active_nodes_count = 0
    
    try:
        # Get application from AppD
        app_data = self.client.get_application(application_name)
        if not app_data:
            logger.warning(f"Application not found in AppD: {application_name}")
            return None
        
        # Save application to database
        app_id = self.db.upsert_application(lob_id, {
            'name': application_name,
            'id': app_data.get('id'),
            'total_tiers': 0,
            'total_nodes': 0,
            'active_nodes': 0,
            'inactive_nodes': 0
        })
        
        # Get all tiers for this application
        tiers = self.client.get_tiers(application_name)
        tiers_count = len(tiers)
        
        for tier in tiers:
            # Save tier
            tier_id = self.db.upsert_tier(app_id, {
                'name': tier['name'],
                'id': tier.get('id'),
                'type': tier.get('type'),
                'total_nodes': 0,
                'active_nodes': 0
            })
            
            # Get all nodes for this tier
            nodes = self.client.get_nodes(application_name, tier['name'])
            
            for node in nodes:
                # Get CPM (Calls Per Minute) metric
                cpm = self.client.get_node_cpm(
                    application_name,
                    node['id']
                )
                
                # Classify as active/inactive
                is_active = cpm >= self.config.APPD_ACTIVE_NODE_THRESHOLD
                
                # Save node with CPM
                self.db.upsert_node(tier_id, app_id, {
                    'name': node['name'],
                    'id': node.get('id'),
                    'machine_name': node.get('machineName'),
                    'ip_address': node.get('ipAddresses', [None])[0],
                    'calls_per_minute': cpm,
                    'threshold': self.config.APPD_ACTIVE_NODE_THRESHOLD,
                    'type': node.get('type'),
                    'agent_version': node.get('agentVersion')
                })
                
                nodes_count += 1
                if is_active:
                    active_nodes_count += 1
        
        # Update application totals
        self.db.upsert_application(lob_id, {
            'name': application_name,
            'id': app_data.get('id'),
            'total_tiers': tiers_count,
            'total_nodes': nodes_count,
            'active_nodes': active_nodes_count,
            'inactive_nodes': nodes_count - active_nodes_count
        })
        
        logger.info(
            f"Discovery complete for {application_name}: "
            f"{tiers_count} tiers, {nodes_count} nodes "
            f"({active_nodes_count} active)"
        )
        
        return {
            'tiers_count': tiers_count,
            'nodes_count': nodes_count,
            'active_nodes_count': active_nodes_count
        }
        
    except Exception as e:
        logger.error(f"Failed to discover {application_name}: {e}")
        raise
```

---

## 🧪 Testing

### Test 1: Save Config First
```bash
curl -X POST http://localhost:8000/api/v1/monitoring/appd/config/save \
  -H "Content-Type: application/json" \
  -d '{
    "config_name": "Digital_tech_CDV3_27Feb_1247",
    "lob_name": "Digital Technology",
    "track": "CDV3",
    "applications": ["icg-tts-paymentinitiation-pte-173720_PTE"]
  }'
```

### Test 2: Run Discovery
```bash
curl -X POST http://localhost:8000/api/v1/monitoring/appd/discovery/run \
  -H "Content-Type: application/json" \
  -d '{
    "config_name": "Digital_tech_CDV3_27Feb_1247",
    "lob_name": "Digital Technology",
    "applications": ["icg-tts-paymentinitiation-pte-173720_PTE"]
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "task_id": "abc123...",
  "status": "initiated",
  "config_name": "Digital_tech_CDV3_27Feb_1247",
  "lob_name": "Digital Technology",
  "applications": ["icg-tts-paymentinitiation-pte-173720_PTE"],
  "message": "Discovery started in background"
}
```

---

## 📋 Summary of Changes

| File | Change | Purpose |
|------|--------|---------|
| `routes.py` | Update `DiscoveryRequest` model | Match UI request format |
| `routes.py` | Update `/discovery/run` endpoint | Accept new format, validate config exists |
| `routes.py` | Update `execute_discovery_task` | Handle per-application discovery |
| `discovery.py` | Add `discover_application` method | Discover single app with stats |

---

## ⚠️ Important Flow

1. **Save Config First** → Creates config in database
2. **Run Discovery** → Uses saved config to discover nodes
3. **Discovery runs in background** → Doesn't block UI
4. **Results saved to database** → Can view via Health Check

---

## 🔍 Check Discovery Results

```sql
-- Check discovery log
SELECT * FROM APPD_DISCOVERY_LOG ORDER BY DISCOVERY_START_TIME DESC;

-- Check discovered applications
SELECT * FROM APPD_APPLICATIONS WHERE LOB_ID = 1;

-- Check discovered nodes
SELECT 
    a.APPLICATION_NAME,
    t.TIER_NAME,
    n.NODE_NAME,
    n.CALLS_PER_MINUTE,
    n.IS_ACTIVE
FROM APPD_APPLICATIONS a
JOIN APPD_TIERS t ON a.APP_ID = t.APP_ID
JOIN APPD_NODES n ON t.TIER_ID = n.TIER_ID
WHERE a.LOB_ID = 1
ORDER BY a.APPLICATION_NAME, t.TIER_NAME, n.NODE_NAME;
```

Apply these changes and the 422 error will be fixed! 🚀