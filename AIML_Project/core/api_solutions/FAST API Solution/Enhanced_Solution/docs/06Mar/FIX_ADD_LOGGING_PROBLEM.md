# 🔧 Fix: Login Hangs After Pool Creation

## 🎯 Problem Identified

- ✅ Database pool creates successfully
- ✅ Pool size and DSN show correctly in logs
- ❌ BUT hangs when you click Login button
- ❌ main.py becomes unresponsive

**Root Cause:** The hang occurs during authentication query execution, not pool creation.

---

## ✅ Solution: Add Detailed Logging to Find Exact Hang Point

### Step 1: Update authentication.py with Debug Logging

**In `authentication.py` (or `02_authentication.py`), find the `authenticate()` method and ADD logging:**

```python
def authenticate(
    self,
    username: str,
    password: str,
    totp_code: str = None,
    ip_address: str = None,
    user_agent: str = None
) -> Optional[Dict]:
    """Authenticate user with password and optional TOTP"""
    
    # ADD THESE LOGS
    logger.info("="*60)
    logger.info(f"AUTHENTICATE CALLED")
    logger.info(f"  Username: {username}")
    logger.info(f"  IP: {ip_address}")
    logger.info(f"  TOTP provided: {totp_code is not None}")
    logger.info("="*60)
    
    conn = None
    cursor = None
    
    try:
        # ADD THIS LOG
        logger.info("Step 1: Acquiring connection from pool...")
        conn = self.pool.acquire()
        logger.info("✓ Step 1: Connection acquired")
        
        # ADD THIS LOG
        logger.info("Step 2: Creating cursor...")
        cursor = conn.cursor()
        logger.info("✓ Step 2: Cursor created")
        
        # ADD THIS LOG
        logger.info("Step 3: Executing query to find user...")
        cursor.execute("""
            SELECT 
                USER_ID, USERNAME, EMAIL, FULL_NAME,
                PASSWORD_HASH, TOTP_SECRET, ROLE,
                IS_ACTIVE, MFA_ENABLED, FAILED_ATTEMPTS,
                LOCKED_UNTIL
            FROM AUTH_USERS
            WHERE USERNAME = :username
        """, {'username': username})
        
        # ADD THIS LOG
        logger.info("✓ Step 3: Query executed")
        logger.info("Step 4: Fetching result...")
        user = cursor.fetchone()
        logger.info(f"✓ Step 4: Fetch complete - User found: {user is not None}")
        
        if not user:
            logger.warning(f"User not found: {username}")
            self._log_audit(username, None, 'FAILED_LOGIN', None, 'N', 'User not found', ip_address)
            return None
        
        # ADD THIS LOG
        logger.info("Step 5: Unpacking user data...")
        (user_id, username, email, full_name, password_hash, 
         totp_secret, role, is_active, mfa_enabled, 
         failed_attempts, locked_until) = user
        logger.info(f"✓ Step 5: User data unpacked - ID: {user_id}, Role: {role}")
        
        # Check if account is active
        logger.info("Step 6: Checking account status...")
        if is_active != 'Y':
            logger.warning(f"Account disabled: {username}")
            self._log_audit(username, user_id, 'FAILED_LOGIN', None, 'N', 'Account disabled', ip_address)
            return None
        logger.info("✓ Step 6: Account is active")
        
        # Check if account is locked
        logger.info("Step 7: Checking account lock status...")
        if locked_until and locked_until > datetime.now():
            remaining = (locked_until - datetime.now()).total_seconds() / 60
            logger.warning(f"Account locked: {username} for {int(remaining)} min")
            self._log_audit(username, user_id, 'FAILED_LOGIN', None, 'N', f'Account locked', ip_address)
            return None
        logger.info("✓ Step 7: Account not locked")
        
        # Verify password
        logger.info("Step 8: Verifying password...")
        if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            logger.warning(f"Invalid password for: {username}")
            self._handle_failed_login(user_id, username, ip_address)
            return None
        logger.info("✓ Step 8: Password verified")
        
        # Verify TOTP (if MFA enabled)
        logger.info(f"Step 9: Checking MFA (enabled={mfa_enabled})...")
        if mfa_enabled == 'Y':
            if not totp_code:
                logger.warning(f"TOTP required but not provided: {username}")
                self._log_audit(username, user_id, 'FAILED_LOGIN', None, 'N', 'TOTP code required', ip_address)
                return None
            
            totp = pyotp.TOTP(totp_secret)
            if not totp.verify(totp_code, valid_window=1):
                logger.warning(f"Invalid TOTP: {username}")
                self._handle_failed_login(user_id, username, ip_address)
                return None
        logger.info("✓ Step 9: MFA check passed")
        
        # Create session
        logger.info("Step 10: Creating session...")
        session_token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(minutes=self.session_expiry_minutes)
        logger.info(f"  Session token: {session_token[:10]}...")
        logger.info(f"  Expires: {expires}")
        
        logger.info("Step 11: Inserting session into database...")
        cursor.execute("""
            INSERT INTO AUTH_SESSIONS (
                SESSION_ID, USER_ID, USERNAME, ROLE,
                IP_ADDRESS, USER_AGENT, EXPIRES_DATE
            ) VALUES (
                :session_id, :user_id, :username, :role,
                :ip, :agent, :expires
            )
        """, {
            'session_id': session_token,
            'user_id': user_id,
            'username': username,
            'role': role,
            'ip': ip_address,
            'agent': user_agent,
            'expires': expires
        })
        logger.info("✓ Step 11: Session inserted")
        
        # Update user
        logger.info("Step 12: Updating user record...")
        cursor.execute("""
            UPDATE AUTH_USERS
            SET FAILED_ATTEMPTS = 0,
                LOCKED_UNTIL = NULL,
                LAST_LOGIN = SYSDATE,
                UPDATED_DATE = SYSDATE
            WHERE USER_ID = :user_id
        """, {'user_id': user_id})
        logger.info("✓ Step 12: User updated")
        
        # Commit
        logger.info("Step 13: Committing transaction...")
        conn.commit()
        logger.info("✓ Step 13: Transaction committed")
        
        # Log audit
        logger.info("Step 14: Logging audit...")
        self._log_audit(username, user_id, 'LOGIN', None, 'Y', None, ip_address, user_agent)
        logger.info("✓ Step 14: Audit logged")
        
        logger.info("="*60)
        logger.info(f"AUTHENTICATION SUCCESSFUL: {username}")
        logger.info("="*60)
        
        return {
            'success': True,
            'session_token': session_token,
            'user_id': user_id,
            'username': username,
            'email': email,
            'full_name': full_name,
            'role': role,
            'expires': expires.isoformat(),
            'expires_in_minutes': self.session_expiry_minutes
        }
        
    except oracledb.Error as e:
        error_obj, = e.args
        logger.error("="*60)
        logger.error("DATABASE ERROR IN AUTHENTICATE")
        logger.error(f"Error Code: {error_obj.code}")
        logger.error(f"Error Message: {error_obj.message}")
        logger.error("="*60)
        if conn:
            conn.rollback()
        return None
    except Exception as e:
        logger.error("="*60)
        logger.error("EXCEPTION IN AUTHENTICATE")
        logger.error(f"Error: {e}", exc_info=True)
        logger.error("="*60)
        if conn:
            conn.rollback()
        return None
    finally:
        # CRITICAL: Always close and release
        logger.info("FINALLY BLOCK: Cleaning up...")
        if cursor:
            try:
                cursor.close()
                logger.info("  ✓ Cursor closed")
            except Exception as e:
                logger.error(f"  Error closing cursor: {e}")
        
        if conn:
            try:
                self.pool.release(conn)
                logger.info("  ✓ Connection released")
            except Exception as e:
                logger.error(f"  Error releasing connection: {e}")
        
        logger.info("FINALLY BLOCK: Complete")
```

---

### Step 2: Update routes.py with Logging

**In `routes.py` (or `03_routes.py`), update the login endpoint:**

```python
@router.post("/login")
async def login(request: LoginRequest, req: Request):
    """Login with username + password + TOTP code"""
    
    logger.info("")
    logger.info("#"*60)
    logger.info("LOGIN ENDPOINT CALLED")
    logger.info(f"  Username: {request.username}")
    logger.info(f"  Password length: {len(request.password)}")
    logger.info(f"  TOTP provided: {request.totp_code is not None}")
    logger.info(f"  IP: {req.client.host}")
    logger.info("#"*60)
    
    try:
        ip_address = req.client.host
        user_agent = req.headers.get('user-agent', 'Unknown')
        
        logger.info("Calling auth_manager.authenticate()...")
        
        result = auth_manager.authenticate(
            username=request.username,
            password=request.password,
            totp_code=request.totp_code,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"auth_manager.authenticate() returned: {result is not None}")
        
        if not result:
            logger.warning("Authentication returned None - login failed")
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials or TOTP code"
            )
        
        logger.info("#"*60)
        logger.info("LOGIN SUCCESSFUL")
        logger.info(f"  Username: {result['username']}")
        logger.info(f"  Role: {result['role']}")
        logger.info("#"*60)
        logger.info("")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("#"*60)
        logger.error("LOGIN ENDPOINT ERROR")
        logger.error(f"Error: {e}", exc_info=True)
        logger.error("#"*60)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
```

---

### Step 3: Enable DEBUG Logging in main.py

**In `main.py` (or `04_main.py`), change logging level:**

```python
# Setup logging - CHANGE TO DEBUG
logging.basicConfig(
    level=logging.DEBUG,  # ← CHANGE from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

---

## 🧪 Testing with Detailed Logs

### Step 1: Restart Server

```bash
# Kill existing process
pkill -f "python main.py"

# Start with debug logging
python main.py

# You should see:
# INFO - Starting application...
# INFO - Database pool created
# ...
```

### Step 2: Try to Login

Open browser, go to `http://localhost:8000/`, enter credentials, click Login.

### Step 3: Watch Terminal Logs

**You should see detailed output like:**

```
INFO - ############################################################
INFO - LOGIN ENDPOINT CALLED
INFO -   Username: admin
INFO -   Password length: 9
INFO -   TOTP provided: False
INFO -   IP: 127.0.0.1
INFO - ############################################################
INFO - Calling auth_manager.authenticate()...
INFO - ============================================================
INFO - AUTHENTICATE CALLED
INFO -   Username: admin
INFO -   IP: 127.0.0.1
INFO -   TOTP provided: False
INFO - ============================================================
INFO - Step 1: Acquiring connection from pool...
INFO - ✓ Step 1: Connection acquired
INFO - Step 2: Creating cursor...
INFO - ✓ Step 2: Cursor created
INFO - Step 3: Executing query to find user...
```

**THE LAST LINE YOU SEE WILL TELL US WHERE IT HANGS!**

---

## 🔍 What to Look For

### If it stops at "Step 3: Executing query..."
**Problem:** Query is hanging
**Solution:** Check AUTH_USERS table, add timeout

### If it stops at "Step 11: Inserting session..."
**Problem:** Can't write to AUTH_SESSIONS table
**Solution:** Check table exists, permissions

### If it stops at "Step 14: Logging audit..."
**Problem:** Can't write to AUTH_AUDIT_LOG table
**Solution:** Check RESOURCE_NAME column fix was applied

### If you see "FINALLY BLOCK" but it hangs there
**Problem:** Can't release connection back to pool
**Solution:** Pool issue, restart Python

---

## 🔧 Quick Checks

### Check 1: Verify Tables Exist

```sql
-- In Oracle
SELECT table_name FROM user_tables WHERE table_name LIKE 'AUTH%';

-- Should show:
-- AUTH_USERS
-- AUTH_SESSIONS
-- AUTH_AUDIT_LOG
-- AUTH_ROLES
```

### Check 2: Verify Auth Schema Applied

```sql
-- Check admin user exists
SELECT username, mfa_enabled, role FROM auth_users;

-- Should show:
-- admin | N | admin
```

### Check 3: Check Table Permissions

```sql
-- Check grants (if using different schema)
SELECT * FROM user_tab_privs WHERE table_name LIKE 'AUTH%';
```

---

## 💡 Alternative: Simplify Authentication Temporarily

**Create a minimal test to isolate the issue:**

```python
# Add this test endpoint to routes.py
@router.get("/test-db")
async def test_database():
    """Test database connection"""
    try:
        conn = auth_manager.pool.acquire()
        cursor = conn.cursor()
        
        # Test 1: Simple query
        cursor.execute("SELECT 1 FROM DUAL")
        result1 = cursor.fetchone()
        
        # Test 2: Query auth_users
        cursor.execute("SELECT COUNT(*) FROM AUTH_USERS")
        result2 = cursor.fetchone()
        
        # Test 3: Insert test audit
        cursor.execute("""
            INSERT INTO AUTH_AUDIT_LOG (
                AUDIT_ID, USERNAME, ACTION, SUCCESS
            ) VALUES (
                AUTH_AUDIT_SEQ.NEXTVAL, 'test', 'TEST', 'Y'
            )
        """)
        conn.commit()
        
        cursor.close()
        auth_manager.pool.release(conn)
        
        return {
            "status": "success",
            "dual_query": result1[0],
            "user_count": result2[0],
            "message": "All database operations work"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

**Test it:**
```bash
curl http://localhost:8000/api/v1/auth/test-db
```

If this works, database is fine. If it hangs, database operations are blocking.

---

## 📊 Expected Normal Output

When working correctly, you should see:

```
[LOGIN ATTEMPT]
Step 1: ✓ Connection acquired
Step 2: ✓ Cursor created
Step 3: ✓ Query executed
Step 4: ✓ Fetch complete - User found: True
Step 5: ✓ User data unpacked
Step 6: ✓ Account is active
Step 7: ✓ Account not locked
Step 8: ✓ Password verified
Step 9: ✓ MFA check passed
Step 10: Creating session...
Step 11: ✓ Session inserted
Step 12: ✓ User updated
Step 13: ✓ Transaction committed
Step 14: ✓ Audit logged
[SUCCESS]
FINALLY BLOCK: Cleaning up...
  ✓ Cursor closed
  ✓ Connection released
```

**Total time: Should be < 1 second**

---

**Apply the logging changes and try again. Share the LAST LINE you see in the logs - that will tell us exactly where it hangs!** 🔍