# TOTP Authentication - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Install Dependencies (1 minute)
```bash
pip install -r requirements.txt --break-system-packages
```

### 2. Setup Database (2 minutes)
```bash
sqlplus your_user/your_pass@your_db @01_database_schema.sql
```

### 3. Configure & Start Backend (1 minute)
```python
# Edit 04_main.py - Update these lines:
DB_CONFIG = {
    'user': 'your_db_user',
    'password': 'your_db_password',
    'dsn': 'localhost:1521/ORCL'
}
```

```bash
python 04_main.py
```

### 4. Test Login (1 minute)
```bash
# Open browser
open http://localhost:8000

# Or open 05_frontend.html directly
open 05_frontend.html

# Login:
Username: admin
Password: Admin@123
TOTP: (leave blank for first login)
```

---

## 📝 Common Tasks

### Create New User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "email": "john@company.com",
    "password": "SecurePass123!",
    "role": "performance_engineer"
  }'
```

### Check Active Sessions
```bash
curl http://localhost:8000/api/v1/auth/sessions \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### View Audit Log
```sql
SELECT 
    USERNAME, ACTION, SUCCESS, TIMESTAMP
FROM AUTH_AUDIT_LOG
WHERE TIMESTAMP > SYSDATE - 1
ORDER BY TIMESTAMP DESC;
```

---

## 🔒 Protect Your Endpoints

### Before (No Auth)
```python
@app.post("/api/v1/monitoring/awr/upload")
async def upload_awr(file: UploadFile):
    # Anyone can upload
    save_awr(file)
```

### After (With Auth)
```python
from auth.routes import require_permission

@app.post("/api/v1/monitoring/awr/upload")
async def upload_awr(
    file: UploadFile,
    user: dict = Depends(require_permission("write"))
):
    # Only users with 'write' permission
    logger.info(f"Upload by {user['username']}")
    save_awr(file, uploaded_by=user['username'])
```

---

## 🎯 Permission Checks

### Check by Permission
```python
user: dict = Depends(require_permission("write"))
user: dict = Depends(require_permission("delete"))
user: dict = Depends(require_permission("configure"))
```

### Check by Role
```python
from auth.routes import require_role

user: dict = Depends(require_role("admin"))
user: dict = Depends(require_role("performance_engineer"))
```

### Check Manually
```python
user: dict = Depends(get_current_user)

if auth_manager.has_permission(user['role'], 'delete'):
    # User can delete
    delete_data()
else:
    raise HTTPException(403, "Cannot delete")
```

---

## 📊 Default Roles & Permissions

| Role | Can Do |
|------|--------|
| **admin** | Everything (read, write, delete, configure, user_manage) |
| **performance_engineer** | Read, write, register tests |
| **test_lead** | Read, write, register tests, approve |
| **viewer** | Read only |

---

## 🔍 Debugging

### Check if auth is working
```python
import requests

# Test health
response = requests.get('http://localhost:8000/api/v1/auth/health')
print(response.json())
# Expected: {"status": "healthy", ...}

# Test login
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'admin',
    'password': 'Admin@123',
    'totp_code': '123456'
})
print(response.json())
# Expected: {"success": true, "session_token": "..."}
```

### Check database
```sql
-- Check users
SELECT USERNAME, ROLE, IS_ACTIVE, MFA_ENABLED FROM AUTH_USERS;

-- Check active sessions
SELECT USERNAME, ROLE, EXPIRES_DATE FROM AUTH_SESSIONS WHERE EXPIRES_DATE > SYSDATE;

-- Check recent logins
SELECT USERNAME, ACTION, SUCCESS, TIMESTAMP 
FROM AUTH_AUDIT_LOG 
WHERE ACTION = 'LOGIN' AND TIMESTAMP > SYSDATE - 1
ORDER BY TIMESTAMP DESC;
```

---

## ⚠️ Important Security Notes

1. **Change default admin password immediately!**
2. **Enable MFA for all users**
3. **Use HTTPS in production**
4. **Rotate passwords every 90 days**
5. **Monitor failed login attempts**
6. **Backup AUTH_USERS table regularly**

---

## 📱 User Setup - Google Authenticator

1. Install Google Authenticator app
2. Admin creates user account
3. User receives QR code
4. User scans QR code in app
5. App shows 6-digit code
6. User logs in with username + password + code

---

## 🎓 Example Integration

### Full Example: Protected AWR Upload

```python
from fastapi import FastAPI, UploadFile, File, Depends
from auth.routes import init_auth_routes, require_permission
import cx_Oracle

app = FastAPI()

# Initialize
db_pool = cx_Oracle.SessionPool(...)
init_auth_routes(db_pool)

@app.post("/api/v1/monitoring/awr/upload")
async def upload_awr_report(
    file: UploadFile = File(...),
    pc_run_id: str = Form(...),
    user: dict = Depends(require_permission("write"))
):
    """Upload AWR report - requires 'write' permission"""
    
    # Log who is uploading
    logger.info(f"AWR upload: {user['username']} (Role: {user['role']})")
    
    # Set Oracle session context
    conn = db_pool.acquire()
    cursor = conn.cursor()
    cursor.execute(
        "BEGIN DBMS_SESSION.SET_IDENTIFIER(:u); END;",
        {'u': user['username']}
    )
    
    # Parse and save
    content = await file.read()
    analysis_id = save_awr_analysis(
        content=content,
        pc_run_id=pc_run_id,
        uploaded_by=user['username']  # Audit trail
    )
    
    cursor.close()
    conn.close()
    
    return {
        'success': True,
        'analysis_id': analysis_id,
        'uploaded_by': user['username']
    }
```

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't login | Check username/password, verify user exists in AUTH_USERS |
| Invalid TOTP | Check phone time is synchronized, try new code |
| 401 Unauthorized | Check Authorization header: `Bearer TOKEN` |
| 403 Permission denied | User role doesn't have required permission |
| Session expired | Login again to get new token |
| Database error | Check DB_CONFIG, verify Oracle is running |

---

## 📞 Testing API with curl

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123","totp_code":""}' \
  | jq -r '.session_token')

# 2. Use token
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 3. Protected endpoint
curl -X POST http://localhost:8000/api/v1/monitoring/awr/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@awr_report.html" \
  -F "pc_run_id=12345"
```

---

**That's it! You now have secure TOTP authentication! 🎉**
