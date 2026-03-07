# TOTP Authentication System - Complete Setup Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Database Setup](#database-setup)
4. [Backend Setup](#backend-setup)
5. [Frontend Setup](#frontend-setup)
6. [First Login](#first-login)
7. [Creating Users](#creating-users)
8. [Integrating with Existing Code](#integrating-with-existing-code)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## 📦 Prerequisites

- Python 3.8 or higher
- Oracle Database 12c or higher
- Oracle Instant Client (for cx_Oracle)
- Google Authenticator app (on mobile phone)

---

## 🚀 Installation Steps

### Step 1: Install Python Dependencies

```bash
# Navigate to the project directory
cd /path/to/totp_auth_complete

# Install all required packages
pip install -r requirements.txt --break-system-packages
```

**Dependencies installed:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pyotp` - TOTP implementation
- `bcrypt` - Password hashing
- `qrcode` - QR code generation
- `cx-Oracle` - Oracle database driver
- `pydantic` - Data validation

---

## 🗄️ Database Setup

### Step 1: Run Database Schema Script

```bash
# Connect to Oracle as your application user
sqlplus your_db_user/your_password@your_database

# Run the schema script
@01_database_schema.sql
```

This will create:
- ✅ `AUTH_USERS` - User accounts table
- ✅ `AUTH_SESSIONS` - Active sessions table
- ✅ `AUTH_AUDIT_LOG` - Authentication audit log
- ✅ `AUTH_ROLES` - Roles and permissions
- ✅ Default admin user (username: `admin`, password: `Admin@123`)

### Step 2: Verify Database Setup

```sql
-- Check tables
SELECT TABLE_NAME FROM USER_TABLES WHERE TABLE_NAME LIKE 'AUTH_%';

-- Expected output:
-- AUTH_USERS
-- AUTH_SESSIONS
-- AUTH_AUDIT_LOG
-- AUTH_ROLES

-- Check default roles
SELECT ROLE_NAME, DESCRIPTION FROM AUTH_ROLES;

-- Expected roles:
-- admin, performance_engineer, test_lead, viewer

-- Check default admin user
SELECT USERNAME, EMAIL, ROLE, IS_ACTIVE, MFA_ENABLED FROM AUTH_USERS;

-- Expected:
-- admin | admin@company.com | admin | Y | N
```

---

## ⚙️ Backend Setup

### Step 1: Configure Database Connection

Edit `04_main.py` and update database credentials:

```python
DB_CONFIG = {
    'user': 'your_db_user',        # Your Oracle username
    'password': 'your_db_password', # Your Oracle password
    'dsn': 'localhost:1521/ORCL',   # Your Oracle DSN
    'min': 2,
    'max': 10,
    'increment': 1
}
```

### Step 2: Copy Files to Your Project

```bash
# Copy authentication files to your project
cp 02_authentication.py /path/to/your/project/auth/authentication.py
cp 03_routes.py /path/to/your/project/auth/routes.py

# Or create auth directory
mkdir -p /path/to/your/project/auth
cp 02_authentication.py /path/to/your/project/auth/
cp 03_routes.py /path/to/your/project/auth/
```

### Step 3: Integrate with Your Existing main.py

In your existing `main.py`, add:

```python
from auth.routes import router as auth_router, init_auth_routes
from auth.routes import get_current_user, require_permission

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    # Your existing initialization
    init_database()
    
    # Initialize authentication
    init_auth_routes(db_pool, session_expiry_minutes=60)

# Include authentication routes
app.include_router(auth_router)
```

### Step 4: Start the Backend

```bash
# Method 1: Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Method 2: Using Python
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     ✓ Database connection pool created
INFO:     ✓ Authentication routes initialized
INFO:     ✓ Application started successfully
```

---

## 🖥️ Frontend Setup

### Option 1: Use Standalone Login Page

```bash
# Open the frontend HTML file in a browser
open 05_frontend.html

# Or copy to your static files directory
cp 05_frontend.html /path/to/your/static/login.html
```

### Option 2: Integrate Login Modal into Existing UI

Add this to your existing `index.html`:

```html
<!-- At the top of <body> -->
<div id="loginModal" style="display: none; position: fixed; ...">
    <!-- Copy login modal HTML from 05_frontend.html -->
</div>

<!-- At the bottom before </body> -->
<script>
    // Copy authentication functions from 05_frontend.html
    let sessionToken = null;
    let currentUser = null;
    
    async function performLogin() { ... }
    async function authenticatedFetch() { ... }
    // ... etc
</script>
```

Update all your API calls to use authenticated fetch:

```javascript
// Before (no authentication)
await fetch('/api/v1/monitoring/awr/upload', {...})

// After (with authentication)
await authenticatedFetch('/api/v1/monitoring/awr/upload', {...})
```

---

## 🔑 First Login

### Step 1: Login as Admin

1. Open your application in browser: `http://localhost:8000`
2. Login with default credentials:
   - Username: `admin`
   - Password: `Admin@123`
   - TOTP Code: Leave blank (MFA not enabled yet)

3. **⚠️ IMPORTANT: Change admin password immediately!**

### Step 2: Enable MFA for Admin

After first login, you need to enable TOTP for admin:

```sql
-- In Oracle, enable MFA for admin
UPDATE AUTH_USERS 
SET MFA_ENABLED = 'Y', 
    TOTP_SECRET = 'JBSWY3DPEHPK3PXP'  -- Example secret
WHERE USERNAME = 'admin';
COMMIT;
```

Generate a new TOTP secret:

```python
# Run this Python script to generate new secret
import pyotp
secret = pyotp.random_base32()
print(f"TOTP Secret: {secret}")

# Generate QR code URL
totp = pyotp.TOTP(secret)
url = totp.provisioning_uri('admin@company.com', 'Monitoring System')
print(f"QR Code URL: {url}")
```

Scan the QR code with Google Authenticator app.

---

## 👥 Creating Users

### Method 1: Using API (Requires Admin Login)

```bash
# Create a new user via API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "username": "john.doe",
    "email": "john@company.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "role": "performance_engineer"
  }'
```

Response includes:
- `totp_secret` - Save this securely!
- `qr_code_base64` - QR code image to scan
- `setup_instructions` - Steps for user

### Method 2: Using Python Script

Create `create_user.py`:

```python
import cx_Oracle
from authentication import AuthenticationManager

# Connect to database
pool = cx_Oracle.SessionPool(
    user='your_user',
    password='your_password',
    dsn='localhost:1521/ORCL',
    min=1, max=1
)

# Create user
auth_manager = AuthenticationManager(pool)
result = auth_manager.create_user(
    username='jane.smith',
    email='jane@company.com',
    password='TempPass456!',
    full_name='Jane Smith',
    role='performance_engineer',
    created_by='admin'
)

print(f"✓ User created: {result['username']}")
print(f"TOTP Secret: {result['totp_secret']}")
print(f"QR Code URL: {result['provisioning_uri']}")

pool.close()
```

Run: `python create_user.py`

### Method 3: Direct SQL (Not Recommended)

Only use for emergency admin account:

```sql
-- Don't use this for normal user creation!
-- This is only for recovery purposes

INSERT INTO AUTH_USERS (
    USER_ID, USERNAME, EMAIL, PASSWORD_HASH, 
    ROLE, IS_ACTIVE, MFA_ENABLED
) VALUES (
    AUTH_USER_SEQ.NEXTVAL,
    'emergency_admin',
    'emergency@company.com',
    '$2b$12$YOUR_BCRYPT_HASH_HERE',
    'admin',
    'Y',
    'N'
);
COMMIT;
```

---

## 🔗 Integrating with Existing Code

### Protect AWR Upload Endpoint

**Before:**
```python
@app.post("/api/v1/monitoring/awr/upload")
async def upload_awr_report(
    file: UploadFile,
    pc_run_id: str
):
    # Anyone can upload
    save_awr_analysis(...)
```

**After:**
```python
from auth.routes import require_permission

@app.post("/api/v1/monitoring/awr/upload")
async def upload_awr_report(
    file: UploadFile,
    pc_run_id: str,
    user: dict = Depends(require_permission("write"))  # ← Add this
):
    # Only users with 'write' permission can upload
    logger.info(f"AWR upload by {user['username']}")
    
    # Set Oracle context with actual username
    set_oracle_user_context(user['username'])
    
    save_awr_analysis(...)
```

### Protect Test Registration

```python
@app.post("/api/v1/pc/test-run/register")
async def register_test(
    pc_run_id: str,
    lob_name: str,
    user: dict = Depends(require_permission("register_test"))  # ← Add this
):
    logger.info(f"Test registration by {user['username']}")
    
    # Save with actual username
    create_master_run(
        ...,
        created_by=user['username']  # ← Audit trail
    )
```

### Set Oracle User Context

```python
def set_oracle_user_context(username: str, conn):
    """Set Oracle session context with authenticated username"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            BEGIN
                DBMS_SESSION.SET_IDENTIFIER(:username);
                DBMS_APPLICATION_INFO.SET_CLIENT_INFO(:username);
            END;
        """, {'username': username})
        conn.commit()
    finally:
        cursor.close()
```

Now all Oracle audit logs will show the actual username!

---

## 🧪 Testing

### Test 1: Health Check

```bash
curl http://localhost:8000/api/v1/auth/health
```

Expected:
```json
{
  "status": "healthy",
  "service": "authentication",
  "auth_enabled": true
}
```

### Test 2: Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@123",
    "totp_code": "123456"
  }'
```

Expected:
```json
{
  "success": true,
  "session_token": "...",
  "user_id": 1,
  "username": "admin",
  "role": "admin",
  "expires": "2026-03-07T15:30:00"
}
```

### Test 3: Protected Endpoint

```bash
# Without token (should fail)
curl http://localhost:8000/api/v1/auth/me

# Expected: 401 Unauthorized

# With token (should work)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"

# Expected: User info
```

### Test 4: Permissions

```bash
# Try to access admin endpoint as viewer
curl http://localhost:8000/api/v1/auth/sessions \
  -H "Authorization: Bearer VIEWER_TOKEN"

# Expected: 403 Permission denied
```

---

## 🔧 Troubleshooting

### Issue 1: "Database connection failed"

**Solution:**
1. Check Oracle database is running
2. Verify DB_CONFIG in main.py
3. Test connection:
   ```python
   import cx_Oracle
   conn = cx_Oracle.connect('user/pass@localhost:1521/ORCL')
   print("✓ Connected")
   conn.close()
   ```

### Issue 2: "Invalid TOTP code"

**Solution:**
1. Check phone time is synchronized
2. Try using valid_window=2 in pyotp.verify()
3. Verify TOTP secret is correct
4. Check time zone settings

### Issue 3: "Session expired immediately"

**Solution:**
1. Check server time vs database time
2. Verify session_expiry_minutes setting
3. Check AUTH_SESSIONS table:
   ```sql
   SELECT SESSION_ID, EXPIRES_DATE, SYSDATE FROM AUTH_SESSIONS;
   ```

### Issue 4: "401 Unauthorized on protected endpoints"

**Solution:**
1. Check Authorization header format: `Bearer TOKEN`
2. Verify token hasn't expired
3. Check token exists in AUTH_SESSIONS table
4. Check user is active:
   ```sql
   SELECT IS_ACTIVE FROM AUTH_USERS WHERE USERNAME = 'your_user';
   ```

### Issue 5: "Cannot create user - unique constraint"

**Solution:**
Username already exists. Use different username or check:
```sql
SELECT USERNAME, IS_ACTIVE FROM AUTH_USERS;
```

---

## 📊 Roles and Permissions Reference

| Role | Permissions | Description |
|------|-------------|-------------|
| **admin** | read, write, delete, configure, user_manage | Full system access |
| **performance_engineer** | read, write, register_test | Can register tests and upload monitoring data |
| **test_lead** | read, write, register_test, approve | Can manage test lifecycle |
| **viewer** | read | Read-only access |

### Adding Custom Permissions

```sql
-- Add new role
INSERT INTO AUTH_ROLES (ROLE_NAME, PERMISSIONS, DESCRIPTION) VALUES (
    'data_analyst',
    '["read","export","analyze"]',
    'Can read and analyze data'
);
COMMIT;

-- Update existing role
UPDATE AUTH_ROLES 
SET PERMISSIONS = '["read","write","export"]'
WHERE ROLE_NAME = 'viewer';
COMMIT;
```

---

## 🎉 Success Checklist

- [ ] Database schema created successfully
- [ ] Default admin user exists
- [ ] Backend starts without errors
- [ ] Can login as admin
- [ ] Created at least one test user
- [ ] User can scan QR code with Google Authenticator
- [ ] TOTP login works
- [ ] Protected endpoints require authentication
- [ ] Permission checking works
- [ ] Audit log records login attempts
- [ ] Session expires correctly
- [ ] Logout works

---

## 📚 Next Steps

1. **Security:**
   - Change default admin password
   - Enable MFA for all users
   - Configure IP whitelisting
   - Set up SSL/TLS certificates

2. **Monitoring:**
   - Check AUTH_AUDIT_LOG regularly
   - Monitor failed login attempts
   - Review active sessions

3. **Maintenance:**
   - Rotate passwords quarterly
   - Remove inactive users
   - Backup AUTH_USERS table
   - Update dependencies

---

## 🆘 Support

If you encounter issues:

1. Check logs: `tail -f app.log`
2. Check database: `SELECT * FROM AUTH_AUDIT_LOG ORDER BY TIMESTAMP DESC`
3. Verify configuration in main.py
4. Test database connection separately

---

**Installation Complete! 🎊**

Your TOTP authentication system is now ready to use.

Default Admin Credentials:
- Username: `admin`
- Password: `Admin@123`
- **⚠️ Change this immediately after first login!**
