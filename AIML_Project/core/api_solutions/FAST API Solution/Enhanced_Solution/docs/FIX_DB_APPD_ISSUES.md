# 🔧 Fix for AppD Database Issues

## Issue 1: JSON LOB Parsing Error
## Issue 2: Missing Columns (CONFIG_NAME, TRACK)

---

## FIX 1: Update database.py - Handle Oracle LOB (CLOB) Objects

The error occurs because Oracle returns CLOB (Character Large Object) instead of string.
You need to READ the CLOB before parsing JSON.

### In `monitoring/appd/database.py`:

Find these methods and update them:

#### Method 1: save_config()
```python
def save_config(self, config_data: dict) -> None:
    """Save AppDynamics configuration to APPD_LOB_CONFIG table"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        # Convert applications list to JSON string
        apps_json = json.dumps(config_data['applications'])
        
        sql = """
            INSERT INTO APPD_LOB_CONFIG (
                LOB_ID,
                CONFIG_NAME,
                LOB_NAME,
                TRACK,
                APPLICATION_NAMES,
                IS_ACTIVE,
                CREATED_DATE,
                UPDATED_DATE
            ) VALUES (
                APPD_LOB_CONFIG_SEQ.NEXTVAL,
                :config_name,
                :lob_name,
                :track,
                :applications,
                :is_active,
                SYSDATE,
                SYSDATE
            )
        """
        
        cursor.execute(sql, {
            'config_name': config_data['config_name'],
            'lob_name': config_data['lob_name'],
            'track': config_data['track'],
            'applications': apps_json,
            'is_active': config_data.get('is_active', 'Y')
        })
        
        conn.commit()
        logger.info(f"Config saved: {config_data['config_name']}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to save config: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
```

#### Method 2: get_config_by_name() - FIX CLOB READING
```python
def get_config_by_name(self, config_name: str) -> dict:
    """Get configuration by config_name"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        sql = """
            SELECT 
                LOB_ID,
                CONFIG_NAME,
                LOB_NAME,
                TRACK,
                APPLICATION_NAMES,
                LAST_DISCOVERY_RUN,
                DISCOVERY_SCHEDULE,
                IS_ACTIVE,
                CREATED_DATE,
                UPDATED_DATE
            FROM APPD_LOB_CONFIG
            WHERE CONFIG_NAME = :config_name
        """
        
        cursor.execute(sql, {'config_name': config_name})
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # ✅ FIX: Handle Oracle CLOB object
        apps_clob = row[4]
        if apps_clob is not None:
            # Read CLOB to string
            if hasattr(apps_clob, 'read'):
                apps_str = apps_clob.read()
            else:
                apps_str = str(apps_clob)
            apps = json.loads(apps_str) if apps_str else []
        else:
            apps = []
        
        return {
            'lob_id': row[0],
            'config_name': row[1],
            'lob_name': row[2],
            'track': row[3],
            'applications': apps,
            'last_discovery_run': row[5].isoformat() if row[5] else None,
            'discovery_schedule': row[6],
            'is_active': row[7],
            'created_date': row[8].isoformat() if row[8] else None,
            'updated_date': row[9].isoformat() if row[9] else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
```

#### Method 3: list_configs() - FIX CLOB READING
```python
def list_configs(self, active_only: bool = True) -> list:
    """List all configurations"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        sql = """
            SELECT 
                LOB_ID,
                CONFIG_NAME,
                LOB_NAME,
                TRACK,
                APPLICATION_NAMES,
                LAST_DISCOVERY_RUN,
                IS_ACTIVE,
                CREATED_DATE
            FROM APPD_LOB_CONFIG
        """
        
        if active_only:
            sql += " WHERE IS_ACTIVE = 'Y'"
        
        sql += " ORDER BY CREATED_DATE DESC"
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        configs = []
        for row in rows:
            # ✅ FIX: Handle Oracle CLOB object
            apps_clob = row[4]
            if apps_clob is not None:
                if hasattr(apps_clob, 'read'):
                    apps_str = apps_clob.read()
                else:
                    apps_str = str(apps_clob)
                apps = json.loads(apps_str) if apps_str else []
            else:
                apps = []
            
            configs.append({
                'lob_id': row[0],
                'config_name': row[1],
                'lob_name': row[2],
                'track': row[3],
                'applications': apps,
                'last_discovery_run': row[5].isoformat() if row[5] else None,
                'is_active': row[6],
                'created_date': row[7].isoformat() if row[7] else None
            })
        
        return configs
        
    except Exception as e:
        logger.error(f"Failed to list configs: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
```

---

## FIX 2: Add Missing Columns to Database

Your `APPD_LOB_CONFIG` table is missing `CONFIG_NAME` and `TRACK` columns.

### Run this SQL to add them:

```sql
-- Add CONFIG_NAME column
ALTER TABLE APPD_LOB_CONFIG 
ADD CONFIG_NAME VARCHAR2(100);

-- Add TRACK column
ALTER TABLE APPD_LOB_CONFIG 
ADD TRACK VARCHAR2(50);

-- Make CONFIG_NAME unique
ALTER TABLE APPD_LOB_CONFIG 
ADD CONSTRAINT UQ_APPD_CONFIG_NAME UNIQUE (CONFIG_NAME);

-- Create index for faster lookups
CREATE INDEX IDX_APPD_CONFIG_NAME ON APPD_LOB_CONFIG(CONFIG_NAME);

-- Verify the changes
SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
FROM USER_TAB_COLUMNS
WHERE TABLE_NAME = 'APPD_LOB_CONFIG'
ORDER BY COLUMN_ID;
```

---

## FIX 3: Alternative - Recreate Table with All Columns

If you want to start fresh, drop and recreate the table:

```sql
-- Drop existing table (BE CAREFUL - THIS DELETES DATA!)
DROP TABLE APPD_LOB_CONFIG CASCADE CONSTRAINTS;
DROP SEQUENCE APPD_LOB_CONFIG_SEQ;

-- Create sequence
CREATE SEQUENCE APPD_LOB_CONFIG_SEQ START WITH 1 INCREMENT BY 1;

-- Create table with ALL columns
CREATE TABLE APPD_LOB_CONFIG (
    LOB_ID NUMBER PRIMARY KEY,
    CONFIG_NAME VARCHAR2(100) UNIQUE NOT NULL,  -- ✅ NEW
    LOB_NAME VARCHAR2(100) NOT NULL,
    TRACK VARCHAR2(50),                          -- ✅ NEW
    LOB_DESCRIPTION VARCHAR2(500),
    APPLICATION_NAMES CLOB,
    LAST_DISCOVERY_RUN TIMESTAMP,
    DISCOVERY_SCHEDULE VARCHAR2(20) DEFAULT 'DAILY',
    IS_ACTIVE CHAR(1) DEFAULT 'Y',
    CREATED_DATE DATE DEFAULT SYSDATE,
    UPDATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT CHK_APPD_LOB_ACTIVE CHECK (IS_ACTIVE IN ('Y', 'N'))
);

-- Create indexes
CREATE INDEX IDX_APPD_LOB_NAME ON APPD_LOB_CONFIG(LOB_NAME);
CREATE INDEX IDX_APPD_CONFIG_NAME ON APPD_LOB_CONFIG(CONFIG_NAME);
CREATE INDEX IDX_APPD_LOB_ACTIVE ON APPD_LOB_CONFIG(IS_ACTIVE);

-- Comments
COMMENT ON TABLE APPD_LOB_CONFIG IS 'AppDynamics LOB configurations with track support';
COMMENT ON COLUMN APPD_LOB_CONFIG.CONFIG_NAME IS 'Unique config identifier (e.g., Retail_Q1_2026)';
COMMENT ON COLUMN APPD_LOB_CONFIG.TRACK IS 'Release/track identifier (e.g., Q1_2026)';
```

---

## 🧪 Testing After Fixes

### Test 1: Save Config
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

### Test 2: List Configs
```bash
curl http://localhost:8000/api/v1/monitoring/appd/config/list
```

### Test 3: Check Database
```sql
SELECT 
    CONFIG_NAME, 
    LOB_NAME, 
    TRACK, 
    DBMS_LOB.SUBSTR(APPLICATION_NAMES, 4000, 1) AS APPS,
    IS_ACTIVE
FROM APPD_LOB_CONFIG;
```

---

## 📋 Summary of Changes

| File | Change | Purpose |
|------|--------|---------|
| `database.py` | Add CLOB reading logic | Fix JSON parsing error |
| `database.py` | Update all config methods | Handle new columns |
| Database | Add `CONFIG_NAME` column | Store unique config ID |
| Database | Add `TRACK` column | Store release track |
| Database | Add unique constraint | Prevent duplicate configs |

---

## ⚠️ Important Notes

1. **CLOB Handling**: Oracle stores JSON in CLOB (Character Large Object) type
2. **Read CLOB**: Must call `.read()` method before `json.loads()`
3. **Column Order**: Make sure SELECT columns match the row[] indices
4. **Backward Compatibility**: Old data without CONFIG_NAME/TRACK will need migration

---

## 🔄 Migration Script (If You Have Existing Data)

If you already have data in the table without CONFIG_NAME/TRACK:

```sql
-- Add columns first
ALTER TABLE APPD_LOB_CONFIG ADD CONFIG_NAME VARCHAR2(100);
ALTER TABLE APPD_LOB_CONFIG ADD TRACK VARCHAR2(50);

-- Populate CONFIG_NAME from existing data
UPDATE APPD_LOB_CONFIG
SET CONFIG_NAME = LOB_NAME || '_' || TO_CHAR(CREATED_DATE, 'DDMONYY_HH24MI')
WHERE CONFIG_NAME IS NULL;

-- Populate TRACK with default value
UPDATE APPD_LOB_CONFIG
SET TRACK = 'DEFAULT'
WHERE TRACK IS NULL;

-- Now make CONFIG_NAME NOT NULL and UNIQUE
ALTER TABLE APPD_LOB_CONFIG MODIFY CONFIG_NAME NOT NULL;
ALTER TABLE APPD_LOB_CONFIG ADD CONSTRAINT UQ_APPD_CONFIG_NAME UNIQUE (CONFIG_NAME);

COMMIT;
```

Apply these fixes and the errors should be resolved! 🚀