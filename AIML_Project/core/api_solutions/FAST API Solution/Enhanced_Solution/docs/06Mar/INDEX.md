# TOTP Authentication System - Complete Package

## 📦 Package Contents

This package contains everything you need to implement secure TOTP (Time-Based One-Time Password) two-factor authentication in your monitoring system.

---

## 📁 Files Included

### 1. Database Setup
- **01_database_schema.sql** (11 KB)
  - Complete Oracle database schema
  - Creates AUTH_USERS, AUTH_SESSIONS, AUTH_AUDIT_LOG, AUTH_ROLES tables
  - Includes default admin user and roles
  - Indexes and views for monitoring
  - Cleanup jobs

### 2. Backend Python Code
- **02_authentication.py** (22 KB)
  - AuthenticationManager class
  - User creation with TOTP secret generation
  - Password hashing with bcrypt
  - Two-factor authentication (password + TOTP)
  - Session management
  - Permission checking
  - Full audit logging

- **03_routes.py** (11 KB)
  - FastAPI authentication routes
  - Login/logout endpoints
  - Protected endpoint decorators
  - Permission and role checking
  - Admin endpoints for user management

- **04_main.py** (6 KB)
  - Complete FastAPI application example
  - Database connection setup
  - Route integration
  - Example protected endpoints

### 3. Frontend
- **05_frontend.html** (21 KB)
  - Complete login interface
  - TOTP code input
  - Session management
  - Auto-login on page load
  - Example of authenticated API calls
  - User dashboard

### 4. Documentation
- **README.md** (14 KB)
  - Complete installation guide
  - Step-by-step setup instructions
  - Database configuration
  - User creation guide
  - Integration examples
  - Troubleshooting guide

- **QUICKSTART.md** (7 KB)
  - 5-minute quick start guide
  - Common tasks reference
  - Debugging tips
  - API testing examples

### 5. Dependencies & Testing
- **requirements.txt** (660 bytes)
  - All Python dependencies listed
  - Ready for pip install

- **test_auth.py** (12 KB)
  - Automated test suite
  - Verifies installation
  - Tests all functionality
  - Provides detailed results

---

## 🚀 Quick Start (5 Minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt --break-system-packages
   ```

2. **Setup database:**
   ```bash
   sqlplus user/pass@db @01_database_schema.sql
   ```

3. **Configure database connection in 04_main.py:**
   ```python
   DB_CONFIG = {
       'user': 'your_user',
       'password': 'your_password',
       'dsn': 'localhost:1521/ORCL'
   }
   ```

4. **Start backend:**
   ```bash
   python 04_main.py
   ```

5. **Open frontend:**
   - Open `05_frontend.html` in browser
   - Or visit `http://localhost:8000`

6. **Login:**
   - Username: `admin`
   - Password: `Admin@123`
   - TOTP: Leave blank (MFA not enabled yet)

---

## 🎯 Key Features

### Security
- ✅ Two-factor authentication (Password + TOTP)
- ✅ Password hashing with bcrypt
- ✅ Session management with expiry
- ✅ Account lockout after 5 failed attempts
- ✅ Full audit trail
- ✅ Role-based access control (RBAC)
- ✅ Permission-based authorization

### Functionality
- ✅ User management (create, update, delete)
- ✅ TOTP secret generation with QR codes
- ✅ Session tracking and management
- ✅ Audit logging (all login/logout events)
- ✅ Active session monitoring
- ✅ IP address and user agent tracking

### Integration
- ✅ Easy integration with existing FastAPI apps
- ✅ Simple decorator-based protection
- ✅ Oracle database integration
- ✅ Complete frontend example
- ✅ RESTful API design

---

## 📊 Default Roles & Permissions

| Role | Permissions | Description |
|------|-------------|-------------|
| **admin** | read, write, delete, configure, user_manage | Full system access |
| **performance_engineer** | read, write, register_test | Register tests, upload data |
| **test_lead** | read, write, register_test, approve | Manage test lifecycle |
| **viewer** | read | Read-only access |

---

## 🔒 How to Protect Your Endpoints

### Step 1: Import dependencies
```python
from auth.routes import get_current_user, require_permission
```

### Step 2: Add dependency to endpoint
```python
@app.post("/api/v1/monitoring/awr/upload")
async def upload_awr(
    file: UploadFile,
    user: dict = Depends(require_permission("write"))
):
    logger.info(f"Upload by {user['username']}")
    # Your existing code...
```

### Step 3: Use user info
```python
# Available in user dict:
user['user_id']       # User ID
user['username']      # Username
user['email']         # Email
user['role']          # Role name
user['permissions']   # List of permissions
```

---

## 🧪 Testing Your Installation

Run the automated test suite:

```bash
python test_auth.py
```

Tests verify:
- ✅ Dependencies installed
- ✅ Server running
- ✅ Database accessible
- ✅ Login working
- ✅ Authentication working
- ✅ Permissions working
- ✅ TOTP generation working
- ✅ Logout working

---

## 💡 Usage Examples

### Create a New User
```python
from authentication import AuthenticationManager

auth_manager = AuthenticationManager(db_pool)

result = auth_manager.create_user(
    username='john.doe',
    email='john@company.com',
    password='SecurePass123!',
    full_name='John Doe',
    role='performance_engineer'
)

print(f"TOTP Secret: {result['totp_secret']}")
print(f"QR Code URL: {result['provisioning_uri']}")
```

### Login
```python
result = auth_manager.authenticate(
    username='john.doe',
    password='SecurePass123!',
    totp_code='123456',  # From Google Authenticator
    ip_address='192.168.1.100'
)

if result:
    session_token = result['session_token']
    print(f"Login successful! Token: {session_token}")
```

### Check Permission
```python
has_write = auth_manager.has_permission('performance_engineer', 'write')
print(f"Can write: {has_write}")  # True
```

---

## 📚 Documentation Structure

```
totp_auth_complete/
├── README.md                    # Complete guide (start here)
├── QUICKSTART.md               # 5-minute quick start
├── 01_database_schema.sql      # Database setup
├── 02_authentication.py        # Core auth logic
├── 03_routes.py                # API endpoints
├── 04_main.py                  # Application integration
├── 05_frontend.html            # Login interface
├── requirements.txt            # Python dependencies
└── test_auth.py               # Automated tests
```

---

## 🔐 Security Best Practices

1. **Change default admin password immediately**
2. **Enable MFA for all users**
3. **Use HTTPS in production**
4. **Rotate passwords every 90 days**
5. **Monitor failed login attempts**
6. **Review active sessions regularly**
7. **Backup AUTH_USERS table**
8. **Use strong passwords (min 12 characters)**
9. **Limit session expiry time (60 minutes recommended)**
10. **Enable IP whitelisting if possible**

---

## 📊 System Requirements

- **Python:** 3.8 or higher
- **Oracle Database:** 12c or higher
- **Browser:** Modern browser (Chrome, Firefox, Edge, Safari)
- **Mobile:** Google Authenticator app (free)

---

## 💰 Cost

**Total Cost: $0**

All components are free:
- ✅ Python libraries (MIT/BSD license)
- ✅ FastAPI (MIT license)
- ✅ Google Authenticator (free app)
- ✅ Oracle database (using existing)

---

## 🆘 Support & Troubleshooting

1. **Read README.md** - Complete installation guide
2. **Read QUICKSTART.md** - Quick reference
3. **Run test_auth.py** - Automated diagnostics
4. **Check logs** - tail -f app.log
5. **Check database** - SELECT * FROM AUTH_AUDIT_LOG

Common issues and solutions are in README.md

---

## ✅ Installation Checklist

- [ ] Read README.md
- [ ] Install Python dependencies
- [ ] Run database schema script
- [ ] Update database config in main.py
- [ ] Start backend server
- [ ] Open frontend in browser
- [ ] Login as admin
- [ ] Change admin password
- [ ] Enable MFA for admin
- [ ] Create test user
- [ ] Test user login with TOTP
- [ ] Run test_auth.py
- [ ] Integrate with your endpoints

---

## 🎉 You're Ready!

This package gives you everything needed for production-ready TOTP authentication:

✅ **Secure** - Industry-standard 2FA
✅ **Free** - $0 cost
✅ **Complete** - Database, backend, frontend included
✅ **Tested** - Automated test suite
✅ **Documented** - Step-by-step guides

---

## 📞 Next Steps

1. Follow README.md for detailed installation
2. Or use QUICKSTART.md for 5-minute setup
3. Run test_auth.py to verify installation
4. Start protecting your endpoints!

**Default Admin Credentials:**
- Username: `admin`
- Password: `Admin@123`
- **⚠️ CHANGE IMMEDIATELY AFTER FIRST LOGIN**

---

**Package Version:** 1.0.0  
**Created:** March 2026  
**License:** MIT (free to use)
