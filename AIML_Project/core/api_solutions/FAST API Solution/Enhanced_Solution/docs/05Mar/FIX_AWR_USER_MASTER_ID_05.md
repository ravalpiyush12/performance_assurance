# 🔧 Fix: AWR Tab - Use Master RUN_ID Not PC_RUN_ID

## 🎯 Problem Identified

**What's happening:**
```
User registers test:
  → PC_RUN_ID: 35678
  → Master RUN_ID: RUNID_35678_04Mar2026_001

User enters in AWR tab:
  → Enters: 35678 (just the PC_RUN_ID)
  
Backend tries to save:
  → INSERT INTO AWR_ANALYSIS_RESULTS (RUN_ID) VALUES ('35678')
  → Foreign key looks for: RUN_MASTER.RUN_ID = '35678'
  → But RUN_MASTER.RUN_ID = 'RUNID_35678_04Mar2026_001'
  → ❌ Parent key not found!
```

**The Issue:**
- Foreign key constraint is on `RUN_MASTER.RUN_ID` (the master run ID)
- Not on `RUN_MASTER.PC_RUN_ID` (the 5-digit number)
- You're providing PC_RUN_ID but database needs master RUN_ID

---

## ✅ Solution: Lookup Master RUN_ID from PC_RUN_ID

### Backend Changes

**File:** `monitoring/awr/routes.py`

**Change the upload endpoint to lookup master RUN_ID:**

```python
@router.post("/awr/upload", response_model=AWRAnalysisResponse)
async def upload_awr_report(
    file: UploadFile = File(...),
    pc_run_id: str = Form(..., description="5-digit PC run ID"),
    database_name: str = Form(...),
    lob_name: str = Form(...),
    track: Optional[str] = Form(None),
    test_name: Optional[str] = Form(None)
):
    """Upload and analyze AWR HTML report"""
    try:
        logger.info(f"Uploading AWR for PC_RUN_ID: {pc_run_id}")
        
        # LOOKUP master RUN_ID from PC_RUN_ID
        master_run = awr_db.get_master_run_by_pc_id(pc_run_id)
        
        if not master_run:
            raise HTTPException(
                status_code=400,
                detail=f"Test not registered. Register PC_RUN_ID {pc_run_id} first."
            )
        
        # Use master RUN_ID from database
        run_id = master_run['run_id']
        logger.info(f"✓ Using master RUN_ID: {run_id}")
        
        # Continue with parsing and analysis...
        # Save with master RUN_ID
        analysis_id = awr_db.save_awr_analysis(
            run_id=run_id,  # ← Master RUN_ID
            ...
        )
```

**Add lookup method to database.py:**

```python
def get_master_run_by_pc_id(self, pc_run_id: str) -> Optional[Dict]:
    """Lookup master RUN_ID from PC_RUN_ID"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT RUN_ID, PC_RUN_ID, LOB_NAME, TEST_NAME
            FROM RUN_MASTER
            WHERE PC_RUN_ID = :pc_run_id
            ORDER BY CREATED_DATE DESC
            FETCH FIRST 1 ROW ONLY
        """, {'pc_run_id': pc_run_id})
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'run_id': row[0],
            'pc_run_id': row[1],
            'lob_name': row[2],
            'test_name': row[3]
        }
    finally:
        cursor.close()
        conn.close()
```

### Frontend Changes

**File:** `index.html`

**Update uploadAWRReport() to use currentTestRun:**

```javascript
async function uploadAWRReport() {
    if (!currentTestRun) {
        alert('Please register test first!');
        return;
    }
    
    // Only send PC_RUN_ID - backend will lookup master RUN_ID
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('pc_run_id', currentTestRun.pc_run_id);  // 5-digit
    formData.append('database_name', dbName);
    formData.append('lob_name', currentTestRun.lob_name);
    
    // Backend returns master RUN_ID in response
}
```

---

## 🧪 Quick Test

```sql
-- Check your RUN_MASTER table
SELECT RUN_ID, PC_RUN_ID FROM RUN_MASTER;

-- You'll see:
-- RUN_ID: RUNID_35678_04Mar2026_001  ← This is what FK needs
-- PC_RUN_ID: 35678                   ← This is what you're sending

-- The fix: Backend looks up full RUN_ID using PC_RUN_ID
```

---

## ✅ Result

**Before:**
```
Send: 35678
FK constraint: RUN_MASTER.RUN_ID = '35678'
Error: Parent key not found ❌
```

**After:**
```
Send: 35678
Backend: SELECT RUN_ID WHERE PC_RUN_ID='35678'
Backend: Gets 'RUNID_35678_04Mar2026_001'
FK constraint: RUN_MASTER.RUN_ID = 'RUNID_35678_04Mar2026_001'
Success! ✓
```

**Apply these changes and it will work!** 🚀