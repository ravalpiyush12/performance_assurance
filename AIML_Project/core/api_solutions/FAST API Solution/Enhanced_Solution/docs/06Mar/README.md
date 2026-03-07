# TOTP Authentication System - python-oracledb 2.0.0

## 🎯 Overview

Complete TOTP (Time-Based One-Time Password) authentication system **updated for python-oracledb 2.0.0**.

**Key Advantage: NO Oracle Instant Client Required!**

---

## 🚀 What's New in This Version

✅ **Uses python-oracledb 2.0.0** (official Oracle driver)  
✅ **Thin Mode** - No Oracle Instant Client needed  
✅ **Pure Python** - Easier deployment  
✅ **Faster** - Optimized connection pooling  
✅ **Better errors** - Clearer error messages  
✅ **Future proof** - Actively maintained by Oracle  

---

## 📦 Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt --break-system-packages
```

**Key dependency: `oracledb==2.0.0`** (replaces cx_Oracle)

### 2. Setup Database
```bash
sqlplus user/pass@db @01_database_schema.sql
```

### 3. Configure Database Connection
Edit `04_main.py`:

```python
DB_CONFIG = {
    'user': 'your_db_user',
    'password': 'your_db_password',
    'dsn': 'localhost:1521/ORCL',  # host:port/service_name
    'min': 2,
    'max': 10
}
```

### 4. Start Server
```bash
python 04_main.py
```

### 5. Login
- Open: `http://localhost:8000`
- Username: `admin`
- Password: `Admin@123`
- TOTP: (leave blank for first login)

---

## 🔑 Key Differences from cx_Oracle Version

| Aspect | cx_Oracle | python-oracledb 2.0.0 |
|--------|-----------|------------------------|
| **Import** | `import cx_Oracle` | `import oracledb` |
| **Pool Creation** | `SessionPool()` | `create_pool()` |
| **Instant Client** | Required | **NOT required** (Thin mode) |
| **Variable Types** | `cx_Oracle.NUMBER` | `int` (Python types) |
| **Performance** | Good | **Better** |
| **Deployment** | Complex | **Simple** |

---

## 📁 Files Included

1. **requirements.txt** - Python dependencies (with oracledb 2.0.0)
2. **01_database_schema.sql** - Database schema (unchanged)
3. **02_authentication.py** - Auth logic (updated for oracledb)
4. **03_routes.py** - FastAPI routes (unchanged)
5. **04_main.py** - Application (updated for oracledb)
6. **05_frontend.html** - Login UI (unchanged)
7. **test_auth.py** - Test suite (unchanged)
8. **MIGRATION_GUIDE.md** - Migration from cx_Oracle
9. **README.md** - This file

---

## 🎯 Features

### Security
- ✅ Two-factor authentication (Password + TOTP)
- ✅ bcrypt password hashing
- ✅ Session expiry (60 min default)
- ✅ Account lockout (5 failed attempts)
- ✅ Full audit trail
- ✅ Role-based access control

### Database
- ✅ **Thin Mode** - No Instant Client!
- ✅ Connection pooling
- ✅ Automatic reconnection
- ✅ Better error handling

### Cost
- ✅ **$0** - All libraries are free

---

## 🔒 Protecting Your Endpoints

```python
from auth.routes import require_permission

@app.post("/api/v1/monitoring/awr/upload")
async def upload_awr(
    file: UploadFile,
    user: dict = Depends(require_permission("write"))
):
    logger.info(f"Upload by {user['username']}")
    
    # Set Oracle session context
    conn = db_pool.acquire()
    cursor = conn.cursor()
    cursor.execute(
        "BEGIN DBMS_SESSION.SET_IDENTIFIER(:u); END;",
        {'u': user['username']}
    )
    cursor.close()
    db_pool.release(conn)
    
    # Your code...
    return {"uploaded_by": user['username']}
```

---

## 🧪 Testing

```bash
# Run automated tests
python test_auth.py
```

Tests verify:
- ✅ oracledb 2.0.0 installed
- ✅ Server running
- ✅ Database connection (Thin mode)
- ✅ Login working
- ✅ Authentication working
- ✅ Permissions working

---

## 🔧 Configuration Options

### Thin Mode (Default - No Instant Client)
```python
pool = oracledb.create_pool(
    user='user',
    password='pass',
    dsn='host:1521/service',
    min=2,
    max=10
)
```

### Thick Mode (With Instant Client)
```python
# Initialize Oracle Client first
oracledb.init_oracle_client(lib_dir="/path/to/instantclient")

# Then create pool
pool = oracledb.create_pool(...)
```

**Use Thin mode unless you need specific Thick mode features!**

---

## 📊 Connection Pool Best Practices

```python
# Acquire connection
conn = pool.acquire()
cursor = conn.cursor()

try:
    # Use connection
    cursor.execute("SELECT ...")
    result = cursor.fetchone()
    conn.commit()
finally:
    # Always release back to pool
    cursor.close()
    pool.release(conn)  # Important!
```

---

## 🆘 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'oracledb'"
```bash
pip install oracledb==2.0.0 --break-system-packages
```

### Error: "DPY-6005: cannot connect to database"
**Check:**
1. Database is running
2. DSN format: `host:port/service_name`
3. Firewall allows port 1521
4. Credentials are correct

**Test connection:**
```python
import oracledb
conn = oracledb.connect(
    user='test',
    password='test',
    dsn='localhost/ORCL'
)
print("✓ Connected")
conn.close()
```

### Error: Variable type issues
```python
# OLD (cx_Oracle)
var = cursor.var(cx_Oracle.NUMBER)

# NEW (oracledb)
var = cursor.var(int)  # Use Python types!
```

---

## 🔄 Migrating from cx_Oracle?

See **MIGRATION_GUIDE.md** for complete migration steps.

**TL;DR:**
1. Uninstall cx_Oracle
2. Install oracledb 2.0.0
3. Change `import cx_Oracle` → `import oracledb`
4. Change `SessionPool()` → `create_pool()`
5. Change variable types to Python types
6. Test!

---

## 📚 Documentation

- **Installation:** This file
- **Migration:** MIGRATION_GUIDE.md
- **API Reference:** See code docstrings
- **Official Docs:** https://python-oracledb.readthedocs.io/

---

## 🎉 Advantages of This Version

### vs cx_Oracle:
✅ **No Instant Client** (Thin mode)  
✅ **Faster** (optimized)  
✅ **Easier deployment** (pure Python)  
✅ **Better errors**  
✅ **Future proof** (maintained)  

### vs API Keys:
✅ **User audit trail** (know who did what)  
✅ **MFA** (password + TOTP)  
✅ **Account lockout** (security)  
✅ **Session management**  
✅ **Role-based access**  

---

## 🚀 Next Steps

1. Install dependencies
2. Setup database
3. Configure DB connection
4. Start server
5. Login and test
6. Protect your endpoints!

---

## 📞 Support

All documentation is self-contained:
- Installation issues? Check this file
- Migration? Check MIGRATION_GUIDE.md
- Testing? Run `python test_auth.py`

---

**Default Admin Credentials:**
- Username: `admin`
- Password: `Admin@123`
- **⚠️ Change immediately after first login!**

---

**This version uses python-oracledb 2.0.0 - No Oracle Instant Client required!** 🎊
