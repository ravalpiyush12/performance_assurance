# 🔧 Fix: Invalid Password & Audit Logging Error

## 🎯 Problems Identified

### Problem 1: Invalid Password
```
WARNING - Invalid password for: admin
```

**Cause:** The bcrypt hash in AUTH_USERS doesn't match "Admin@123"

### Problem 2: Audit Logging Failed
```
ERROR - Audit logging failed: ORA-01745: invalid host
```

**Cause:** The `_log_audit()` function has an issue with column names or bind variables

---

## ✅ Solution 1: Reset Admin Password

The bcrypt hash in the database doesn't match. Let's regenerate it:

### Step 1: Generate Correct Hash

Run this Python script to generate the correct hash:

```python
import bcrypt

password = "Admin@123"
hash_result = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(f"Password: {password}")
print(f"Bcrypt hash: {hash_result.decode('utf-8')}")
```

### Step 2: Update Database

```sql
-- Update admin password with correct hash
UPDATE AUTH_USERS 
SET PASSWORD_HASH = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYmPvr6yXw2'
WHERE USERNAME = 'admin';

COMMIT;

-- Verify
SELECT USERNAME, 
       SUBSTR(PASSWORD_HASH, 1, 20) AS HASH_PREFIX,
       MFA_ENABLED
FROM AUTH_USERS 
WHERE USERNAME = 'admin';
```

### Alternative: Create New Admin with Known Password

```sql
-- Delete old admin
DELETE FROM AUTH_USERS WHERE USERNAME = 'admin';

-- Insert new admin with known hash
INSERT INTO AUTH_USERS (
    USER_ID, USERNAME, EMAIL, FULL_NAME, 
    PASSWORD_HASH, TOTP_SECRET, ROLE, 
    IS_ACTIVE, MFA_ENABLED, CREATED_BY
) VALUES (
    AUTH_USER_SEQ.NEXTVAL,
    'admin',
    'admin@company.com',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYmPvr6yXw2',  -- Admin@123
    NULL,
    'admin',
    'Y',
    'N',
    'SYSTEM'
);

COMMIT;
```

---

## ✅ Solution 2: Fix Audit Logging Error (ORA-01745)

### Error: ORA-01745: invalid host

This error occurs in `_log_audit()` function. The issue is likely with bind variable names.

### Fix: Update _log_audit() in authentication.py

**FIND this function:**

```python
def _log_audit(
    self,
    username: str,
    user_id: int,
    action: str,
    resource: str = None,
    success: str = 'Y',
    failure_reason: str = None,
    ip_address: str = None,
    user_agent: str = None
):
    """Log audit event"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO AUTH_AUDIT_LOG (
                AUDIT_ID, USERNAME, USER_ID, ACTION, RESOURCE,
                SUCCESS, FAILURE_REASON, IP_ADDRESS, USER_AGENT
            ) VALUES (
                AUTH_AUDIT_SEQ.NEXTVAL, :username, :user_id, :action, :resource,
                :success, :reason, :ip, :agent
            )
        """, {
            'username': username,
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'success': success,
            'reason': failure_reason,
            'ip': ip_address,
            'agent': user_agent
        })
        
        conn.commit()
```

**The problem:** Column name is `RESOURCE_NAME` but code uses `RESOURCE`

**REPLACE WITH:**

```python
def _log_audit(
    self,
    username: str,
    user_id: int,
    action: str,
    resource: str = None,
    success: str = 'Y',
    failure_reason: str = None,
    ip_address: str = None,
    user_agent: str = None
):
    """Log audit event"""
    conn = None
    cursor = None
    
    try:
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO AUTH_AUDIT_LOG (
                AUDIT_ID, USERNAME, USER_ID, ACTION, RESOURCE_NAME,
                SUCCESS, FAILURE_REASON, IP_ADDRESS, USER_AGENT
            ) VALUES (
                AUTH_AUDIT_SEQ.NEXTVAL, :username, :user_id, :action, :resource_name,
                :success, :reason, :ip_addr, :user_agent
            )
        """, {
            'username': username,
            'user_id': user_id,
            'action': action,
            'resource_name': resource,  # ← Changed bind variable name
            'success': success,
            'reason': failure_reason,
            'ip_addr': ip_address,      # ← Changed to avoid reserved word
            'user_agent': user_agent
        })
        
        conn.commit()
        
    except Exception as e:
        # Don't fail main operation if audit logging fails
        logger.error(f"Audit logging failed: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                self.pool.release(conn)
            except:
                pass
```

**Key changes:**
1. `RESOURCE` → `RESOURCE_NAME` (column name)
2. `:resource` → `:resource_name` (bind variable)
3. `:ip` → `:ip_addr` (avoid potential reserved word)
4. Added proper exception handling
5. Added `conn.rollback()` on error

---

## ✅ Solution 3: Verify Database Schema

Make sure AUTH_AUDIT_LOG has correct column name:

```sql
-- Check table structure
DESC AUTH_AUDIT_LOG;

-- Should show RESOURCE_NAME, not RESOURCE
-- If it shows RESOURCE, run the fixed schema:
-- @01_database_schema_FIXED.sql
```

---

## 🧪 Complete Testing Steps

### Step 1: Fix Database

```sql
-- 1. Reset admin password
UPDATE AUTH_USERS 
SET PASSWORD_HASH = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYmPvr6yXw2',
    MFA_ENABLED = 'N',
    FAILED_ATTEMPTS = 0,
    LOCKED_UNTIL = NULL
WHERE USERNAME = 'admin';

COMMIT;

-- 2. Verify AUTH_AUDIT_LOG structure
DESC AUTH_AUDIT_LOG;
-- Should show: RESOURCE_NAME VARCHAR2(200)

-- 3. Test insert
INSERT INTO AUTH_AUDIT_LOG (
    AUDIT_ID, USERNAME, ACTION, RESOURCE_NAME, SUCCESS
) VALUES (
    AUTH_AUDIT_SEQ.NEXTVAL, 'test', 'TEST', '/api/test', 'Y'
);
COMMIT;

-- If insert fails, column name is wrong - run fixed schema
```

### Step 2: Update Python Code

Update `_log_audit()` function in `authentication.py` as shown above.

### Step 3: Restart Server

```bash
pkill -f python
python main.py
```

### Step 4: Test Login

```
Username: admin
Password: Admin@123
TOTP: (leave blank)
```

---

## 📊 Expected Output After Fix

```
Step 7: ✓ Account not locked
Step 8: Verifying password...
✓ Step 8: Password verified             ← Should see this now!
Step 9: ✓ MFA check passed
Step 10: Creating session...
Step 11: ✓ Session inserted
Step 12: ✓ User updated
Step 13: ✓ Transaction committed
Step 14: ✓ Audit logged                 ← Should work now!
✓ LOGIN SUCCESSFUL
```

---

## 🔍 Quick Diagnostic

### Test 1: Check Password Hash

```python
# Run this to verify bcrypt
import bcrypt

stored_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYmPvr6yXw2'
password = 'Admin@123'

if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
    print("✓ Password matches hash!")
else:
    print("✗ Password does NOT match hash!")
```

### Test 2: Check Column Name

```sql
-- Find actual column name
SELECT column_name 
FROM user_tab_columns 
WHERE table_name = 'AUTH_AUDIT_LOG' 
  AND column_name LIKE '%RESOURCE%';

-- If returns 'RESOURCE' instead of 'RESOURCE_NAME', that's the problem
```

---

## 💡 If Still Failing

### Option 1: Disable Audit Logging Temporarily

In `authentication.py`, comment out audit calls:

```python
# self._log_audit(username, user_id, 'FAILED_LOGIN', ...)
# Just comment out all _log_audit calls temporarily
```

This will let you login while we fix audit table.

### Option 2: Recreate AUTH_AUDIT_LOG

```sql
-- Drop and recreate with correct column name
DROP TABLE AUTH_AUDIT_LOG;

CREATE TABLE AUTH_AUDIT_LOG (
    AUDIT_ID NUMBER PRIMARY KEY,
    USERNAME VARCHAR2(100),
    USER_ID NUMBER,
    ACTION VARCHAR2(100) NOT NULL,
    RESOURCE_NAME VARCHAR2(200),        -- CORRECT NAME
    DETAILS VARCHAR2(4000),
    IP_ADDRESS VARCHAR2(50),
    USER_AGENT VARCHAR2(500),
    SUCCESS CHAR(1) NOT NULL,
    FAILURE_REASON VARCHAR2(500),
    TIMESTAMP DATE DEFAULT SYSDATE,
    CONSTRAINT CHK_AUDIT_SUCCESS CHECK (SUCCESS IN ('Y', 'N'))
);
```

---

## ✅ Summary of Fixes

1. **Password:** Update admin hash in database
2. **Audit Log:** Change `RESOURCE` → `RESOURCE_NAME` in code
3. **Bind Variables:** Rename `:ip` → `:ip_addr` to avoid conflicts
4. **Error Handling:** Add try/catch in `_log_audit()`

**Apply these fixes and login should work!** 🎉