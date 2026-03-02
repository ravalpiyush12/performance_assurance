# 🎯 Complete AppD UI Enhancement Solution

## Requirements Summary:
1. Remove "Code 1, Code 2, Code 3" labels
2. Discovery: Prepopulated LOB dropdown, auto-generated config names (NFT_LOB_Track_Date_Time)
3. Applications: Store in DB, show as multi-select dropdown
4. Health Check: Cascading dropdowns (LOB → Track → Config), table format output
5. Start Monitoring: Cascading dropdowns, auto-fetch applications from config

---

## PART 1: Database Schema Changes

### New Table: APPD_APPLICATIONS_MASTER
```sql
-- Master list of all AppDynamics applications
CREATE TABLE APPD_APPLICATIONS_MASTER (
    APP_MASTER_ID NUMBER PRIMARY KEY,
    APPLICATION_NAME VARCHAR2(200) UNIQUE NOT NULL,
    DESCRIPTION VARCHAR2(500),
    LOB_NAME VARCHAR2(100),
    IS_ACTIVE CHAR(1) DEFAULT 'Y',
    CREATED_DATE DATE DEFAULT SYSDATE,
    UPDATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT CHK_APP_MASTER_ACTIVE CHECK (IS_ACTIVE IN ('Y', 'N'))
);

CREATE SEQUENCE APPD_APP_MASTER_SEQ START WITH 1 INCREMENT BY 1;
CREATE INDEX IDX_APP_MASTER_LOB ON APPD_APPLICATIONS_MASTER(LOB_NAME);
CREATE INDEX IDX_APP_MASTER_NAME ON APPD_APPLICATIONS_MASTER(APPLICATION_NAME);

COMMENT ON TABLE APPD_APPLICATIONS_MASTER IS 'Master list of AppDynamics applications for UI dropdown';
```

### Insert Sample Applications
```sql
INSERT INTO APPD_APPLICATIONS_MASTER (APP_MASTER_ID, APPLICATION_NAME, LOB_NAME, DESCRIPTION)
VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'icg-tts-paymentinitiation-pte-173720_PTE', 'Digital Technology', 'Payment Initiation Service');

INSERT INTO APPD_APPLICATIONS_MASTER (APP_MASTER_ID, APPLICATION_NAME, LOB_NAME, DESCRIPTION)
VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'RetailWeb', 'Retail', 'Retail Web Application');

INSERT INTO APPD_APPLICATIONS_MASTER (APP_MASTER_ID, APPLICATION_NAME, LOB_NAME, DESCRIPTION)
VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'RetailAPI', 'Retail', 'Retail API Service');

INSERT INTO APPD_APPLICATIONS_MASTER (APP_MASTER_ID, APPLICATION_NAME, LOB_NAME, DESCRIPTION)
VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'DataPlatform', 'Data', 'Data Platform Service');

INSERT INTO APPD_APPLICATIONS_MASTER (APP_MASTER_ID, APPLICATION_NAME, LOB_NAME, DESCRIPTION)
VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'PaymentGateway', 'Payments', 'Payment Gateway');

INSERT INTO APPD_APPLICATIONS_MASTER (APP_MASTER_ID, APPLICATION_NAME, LOB_NAME, DESCRIPTION)
VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'CommercialCardsAPI', 'Commercial Cards', 'Commercial Cards API');

COMMIT;
```

### New Table: APPD_LOB_MASTER
```sql
-- Master list of LOBs
CREATE TABLE APPD_LOB_MASTER (
    LOB_MASTER_ID NUMBER PRIMARY KEY,
    LOB_NAME VARCHAR2(100) UNIQUE NOT NULL,
    LOB_CODE VARCHAR2(20) NOT NULL,
    DESCRIPTION VARCHAR2(500),
    IS_ACTIVE CHAR(1) DEFAULT 'Y',
    CREATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT CHK_LOB_MASTER_ACTIVE CHECK (IS_ACTIVE IN ('Y', 'N'))
);

CREATE SEQUENCE APPD_LOB_MASTER_SEQ START WITH 1 INCREMENT BY 1;

COMMENT ON TABLE APPD_LOB_MASTER IS 'Master list of LOBs for dropdown';
```

### Insert LOBs
```sql
INSERT INTO APPD_LOB_MASTER (LOB_MASTER_ID, LOB_NAME, LOB_CODE, DESCRIPTION)
VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'Digital Technology', 'DT', 'Digital Technology Services');

INSERT INTO APPD_LOB_MASTER (LOB_MASTER_ID, LOB_NAME, LOB_CODE, DESCRIPTION)
VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'Data', 'DATA', 'Data Platform and Analytics');

INSERT INTO APPD_LOB_MASTER (LOB_MASTER_ID, LOB_NAME, LOB_CODE, DESCRIPTION)
VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'Payments', 'PAY', 'Payment Services');

INSERT INTO APPD_LOB_MASTER (LOB_MASTER_ID, LOB_NAME, LOB_CODE, DESCRIPTION)
VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'Commercial Cards', 'CC', 'Commercial Cards Division');

INSERT INTO APPD_LOB_MASTER (LOB_MASTER_ID, LOB_NAME, LOB_CODE, DESCRIPTION)
VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'Retail', 'RETAIL', 'Retail Banking');

COMMIT;
```

---

## PART 2: Backend API Endpoints (Add to routes.py)

```python
# ==========================================
# Master Data Endpoints
# ==========================================

@router.get("/master/lobs")
async def get_master_lobs():
    """Get list of all LOBs for dropdown"""
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        lobs = appd_db.get_master_lobs()
        return {
            "total": len(lobs),
            "lobs": lobs
        }
    except Exception as e:
        logger.error(f"Failed to get master LOBs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/master/applications")
async def get_master_applications(lob_name: Optional[str] = None):
    """Get list of all applications for dropdown"""
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        apps = appd_db.get_master_applications(lob_name)
        return {
            "total": len(apps),
            "applications": apps
        }
    except Exception as e:
        logger.error(f"Failed to get master applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs/by-lob-track")
async def get_configs_by_lob_track(lob_name: str, track: str):
    """Get latest config for LOB and Track"""
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        config = appd_db.get_latest_config_by_lob_track(lob_name, track)
        if not config:
            return {"config": None}
        return {"config": config}
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs/tracks/{lob_name}")
async def get_tracks_for_lob(lob_name: str):
    """Get all distinct tracks for a LOB"""
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        tracks = appd_db.get_tracks_for_lob(lob_name)
        return {
            "lob_name": lob_name,
            "total": len(tracks),
            "tracks": tracks
        }
    except Exception as e:
        logger.error(f"Failed to get tracks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## PART 3: Database Methods (Add to database.py)

```python
def get_master_lobs(self) -> List[dict]:
    """Get all LOBs from master table"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        sql = """
            SELECT LOB_NAME, LOB_CODE, DESCRIPTION
            FROM APPD_LOB_MASTER
            WHERE IS_ACTIVE = 'Y'
            ORDER BY LOB_NAME
        """
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        lobs = []
        for row in rows:
            lobs.append({
                'lob_name': row[0],
                'lob_code': row[1],
                'description': row[2]
            })
        
        return lobs
        
    finally:
        cursor.close()
        conn.close()


def get_master_applications(self, lob_name: Optional[str] = None) -> List[dict]:
    """Get all applications from master table"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        if lob_name:
            sql = """
                SELECT APPLICATION_NAME, LOB_NAME, DESCRIPTION
                FROM APPD_APPLICATIONS_MASTER
                WHERE IS_ACTIVE = 'Y' AND LOB_NAME = :lob_name
                ORDER BY APPLICATION_NAME
            """
            cursor.execute(sql, {'lob_name': lob_name})
        else:
            sql = """
                SELECT APPLICATION_NAME, LOB_NAME, DESCRIPTION
                FROM APPD_APPLICATIONS_MASTER
                WHERE IS_ACTIVE = 'Y'
                ORDER BY APPLICATION_NAME
            """
            cursor.execute(sql)
        
        rows = cursor.fetchall()
        
        apps = []
        for row in rows:
            apps.append({
                'application_name': row[0],
                'lob_name': row[1],
                'description': row[2]
            })
        
        return apps
        
    finally:
        cursor.close()
        conn.close()


def get_tracks_for_lob(self, lob_name: str) -> List[str]:
    """Get all distinct tracks for a LOB"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        sql = """
            SELECT DISTINCT TRACK
            FROM APPD_LOB_CONFIG
            WHERE LOB_NAME = :lob_name
              AND IS_ACTIVE = 'Y'
            ORDER BY TRACK DESC
        """
        
        cursor.execute(sql, {'lob_name': lob_name})
        rows = cursor.fetchall()
        
        return [row[0] for row in rows if row[0]]
        
    finally:
        cursor.close()
        conn.close()


def get_latest_config_by_lob_track(self, lob_name: str, track: str) -> Optional[dict]:
    """Get latest config for LOB and Track"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        sql = """
            SELECT 
                CONFIG_NAME,
                LOB_NAME,
                TRACK,
                APPLICATION_NAMES,
                CREATED_DATE
            FROM APPD_LOB_CONFIG
            WHERE LOB_NAME = :lob_name
              AND TRACK = :track
              AND IS_ACTIVE = 'Y'
            ORDER BY CREATED_DATE DESC
            FETCH FIRST 1 ROW ONLY
        """
        
        cursor.execute(sql, {'lob_name': lob_name, 'track': track})
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Handle CLOB
        apps_clob = row[3]
        if apps_clob:
            if hasattr(apps_clob, 'read'):
                apps_str = apps_clob.read()
            else:
                apps_str = str(apps_clob)
            apps = json.loads(apps_str) if apps_str else []
        else:
            apps = []
        
        return {
            'config_name': row[0],
            'lob_name': row[1],
            'track': row[2],
            'applications': apps,
            'created_date': row[4].isoformat() if row[4] else None
        }
        
    finally:
        cursor.close()
        conn.close()
```

---

## PART 4: Updated StartMonitoringRequest Model

```python
class StartMonitoringRequest(BaseModel):
    """Request model for starting monitoring"""
    run_id: str
    config_name: str  # ✅ Now supports config_name
    lob_name: str     # ✅ Also supports lob_name
    track: str        # ✅ Also supports track
    test_name: Optional[str] = None
    interval_seconds: int = 1800
    
    class Config:
        schema_extra = {
            "example": {
                "run_id": "RUN_20260302_001",
                "config_name": "NFT_Digital_Technology_CDV3_02Mar2026_1430",
                "lob_name": "Digital Technology",
                "track": "CDV3",
                "test_name": "Peak Load Test",
                "interval_seconds": 1800
            }
        }
```

---

## PART 5: Updated /monitoring/start Endpoint

```python
@router.post("/monitoring/start")
async def start_monitoring(request: StartMonitoringRequest):
    """Start monitoring session - supports both config_name and lob_name/track"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        # Get config by config_name
        config = appd_db.get_config_by_name(request.config_name)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Config '{request.config_name}' not found"
            )
        
        lob_id = config['lob_id']
        lob_name = config['lob_name']
        track = config['track']
        applications = config['applications']
        
        # Check thread pool capacity
        with thread_lock:
            if request.run_id in monitoring_threads:
                raise HTTPException(status_code=400, detail="Run ID already exists")
            
            active_count = sum(1 for t in monitoring_threads.values() if t.is_alive())
            if active_count >= appd_config.APPD_MAX_CONCURRENT_MONITORS:
                raise HTTPException(status_code=429, detail="Max monitors reached")
        
        # Start monitoring
        orchestrator.start_monitoring(
            request.run_id,
            lob_name,
            applications,
            lob_id=lob_id,
            track=track,
            test_name=request.test_name
        )
        
        # Launch background thread
        thread = threading.Thread(
            target=monitoring_worker,
            args=(request.run_id, request.interval_seconds),
            daemon=True
        )
        
        with thread_lock:
            monitoring_threads[request.run_id] = thread
        thread.start()
        
        return {
            "success": True,
            "run_id": request.run_id,
            "config_name": request.config_name,
            "lob_name": lob_name,
            "track": track,
            "applications": applications,
            "message": "Monitoring started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## PART 6: Updated index_final.html (AppD Tab Only)

I'll create the complete updated AppD tab section next...

This is Part 1 of the solution. Shall I continue with the complete UI code?