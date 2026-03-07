# Migration Guide: cx_Oracle → python-oracledb 2.0.0

## 🎯 Why Migrate?

**python-oracledb 2.0.0** (the new official Oracle driver) offers:

✅ **No Oracle Instant Client required** (Thin mode)  
✅ **Faster performance** (optimized connection pooling)  
✅ **Pure Python** (easier deployment)  
✅ **Better error messages**  
✅ **Actively maintained** by Oracle  
✅ **Backward compatible** (mostly drop-in replacement)  

---

## 📋 Key Changes

### 1. Import Statement
```python
# OLD (cx_Oracle)
import cx_Oracle

# NEW (python-oracledb)
import oracledb
```

### 2. Connection Pool Creation
```python
# OLD (cx_Oracle)
pool = cx_Oracle.SessionPool(
    user='user',
    password='pass',
    dsn='localhost:1521/ORCL',
    min=2,
    max=10,
    increment=1,
    threaded=True
)

# NEW (python-oracledb 2.0.0)
pool = oracledb.create_pool(
    user='user',
    password='pass',
    dsn='localhost:1521/ORCL',
    min=2,
    max=10,
    increment=1,
    threaded=True,
    events=True  # NEW: Enable event handling
)
```

### 3. Connection Management
```python
# OLD (cx_Oracle)
conn = pool.acquire()
# ... use connection ...
conn.close()

# NEW (python-oracledb) - Same!
conn = pool.acquire()
# ... use connection ...
pool.release(conn)  # Or conn.close()
```

### 4. Variable Creation (RETURNING clause)
```python
# OLD (cx_Oracle)
user_id_var = cursor.var(cx_Oracle.NUMBER)

# NEW (python-oracledb)
user_id_var = cursor.var(int)  # Use Python types!
```

### 5. Getting Variable Value
```python
# OLD (cx_Oracle)
user_id = int(cursor.getvalue()[0])

# NEW (python-oracledb) - Same!
user_id = user_id_var.getvalue()[0]
```

### 6. Exception Handling
```python
# OLD (cx_Oracle)
except cx_Oracle.IntegrityError:
    ...
except cx_Oracle.Error as e:
    error_obj, = e.args
    print(error_obj.message)

# NEW (python-oracledb) - Same!
except oracledb.IntegrityError:
    ...
except oracledb.Error as e:
    error_obj, = e.args
    print(error_obj.message)
```

---

## 🔄 Complete Migration Steps

### Step 1: Uninstall cx_Oracle
```bash
pip uninstall cx-Oracle
```

### Step 2: Install python-oracledb 2.0.0
```bash
pip install oracledb==2.0.0 --break-system-packages
```

### Step 3: Update Imports
Find and replace in all Python files:
```bash
# Find
import cx_Oracle

# Replace with
import oracledb
```

### Step 4: Update Pool Creation
```python
# Change from
pool = cx_Oracle.SessionPool(...)

# To
pool = oracledb.create_pool(...)
```

### Step 5: Update Variable Types
```python
# Change from
var = cursor.var(cx_Oracle.NUMBER)
var = cursor.var(cx_Oracle.STRING)

# To
var = cursor.var(int)
var = cursor.var(str)
```

### Step 6: Update Exception Names
```python
# Change from
except cx_Oracle.Error:
except cx_Oracle.IntegrityError:

# To
except oracledb.Error:
except oracledb.IntegrityError:
```

---

## 📊 Side-by-Side Comparison

| Feature | cx_Oracle | python-oracledb 2.0.0 |
|---------|-----------|------------------------|
| **Import** | `import cx_Oracle` | `import oracledb` |
| **Pool** | `SessionPool()` | `create_pool()` |
| **Instant Client** | Required | Optional (Thin mode!) |
| **Variable Types** | `cx_Oracle.NUMBER` | `int` (Python types) |
| **Performance** | Good | Better (optimized) |
| **Maintenance** | Deprecated | Actively maintained |
| **Python Support** | 3.6+ | 3.7+ |

---

## 🚀 Thin Mode vs Thick Mode

### Thin Mode (Default - Recommended)
```python
# Just create the pool - uses Thin mode automatically
pool = oracledb.create_pool(
    user='user',
    password='pass',
    dsn='host:1521/service'
)
```

**Advantages:**
- ✅ No Oracle Instant Client needed
- ✅ Pure Python
- ✅ Easier deployment
- ✅ Smaller footprint

**Limitations:**
- ⚠️ Some advanced features not available
- ⚠️ Different network protocol

### Thick Mode (Optional)
```python
# Initialize Oracle Client first
oracledb.init_oracle_client(lib_dir="/path/to/instantclient")

# Then create pool
pool = oracledb.create_pool(...)
```

**Use when:**
- Need features only in Thick mode
- Required by existing infrastructure
- Need exact cx_Oracle compatibility

---

## 🛠️ Code Changes Summary

### authentication.py
```python
# Line 1: Import
import oracledb  # Was: import cx_Oracle

# Line 15: Exception handling
except oracledb.IntegrityError as e:  # Was: cx_Oracle.IntegrityError

# Line 40: Variable creation
user_id_var = cursor.var(int)  # Was: cursor.var(cx_Oracle.NUMBER)

# Line 45: Pool release
self.pool.release(conn)  # Was: conn.close()
```

### main.py
```python
# Line 1: Import
import oracledb  # Was: import cx_Oracle

# Line 20: Pool creation
pool = oracledb.create_pool(...)  # Was: cx_Oracle.SessionPool(...)

# Line 30: Exception
except oracledb.Error as e:  # Was: cx_Oracle.Error
```

---

## ✅ Testing After Migration

### Test 1: Import
```python
import oracledb
print(f"✓ oracledb version: {oracledb.__version__}")
# Expected: 2.0.0
```

### Test 2: Connection
```python
pool = oracledb.create_pool(
    user='test',
    password='test',
    dsn='localhost/ORCL',
    min=1,
    max=1
)
conn = pool.acquire()
print("✓ Connection successful")
pool.release(conn)
pool.close()
```

### Test 3: Query
```python
conn = pool.acquire()
cursor = conn.cursor()
cursor.execute("SELECT 'Hello from oracledb!' FROM DUAL")
result = cursor.fetchone()
print(f"✓ Query result: {result[0]}")
cursor.close()
pool.release(conn)
```

### Test 4: Run Test Suite
```bash
python test_auth.py
```

All tests should pass!

---

## 🔍 Troubleshooting

### Issue 1: Import Error
```
ModuleNotFoundError: No module named 'oracledb'
```

**Solution:**
```bash
pip install oracledb==2.0.0 --break-system-packages
```

### Issue 2: Connection Error (Thin mode)
```
DPY-6005: cannot connect to database
```

**Solution:**
- Check firewall allows port 1521
- Verify DSN format: `host:port/service_name`
- Try Thick mode if needed

### Issue 3: Variable Type Error
```
TypeError: expecting int or a DB API type
```

**Solution:**
Change from:
```python
var = cursor.var(cx_Oracle.NUMBER)
```

To:
```python
var = cursor.var(int)
```

---

## 📚 Resources

- **Official Docs:** https://python-oracledb.readthedocs.io/
- **Migration Guide:** https://python-oracledb.readthedocs.io/en/latest/user_guide/appendix_a.html
- **Release Notes:** https://python-oracledb.readthedocs.io/en/latest/release_notes.html
- **GitHub:** https://github.com/oracle/python-oracledb

---

## 🎉 Benefits After Migration

✅ **Simpler Deployment** - No Instant Client installation  
✅ **Faster Startup** - Optimized connection pooling  
✅ **Better Errors** - Clearer error messages  
✅ **Future Proof** - Actively maintained by Oracle  
✅ **Docker Friendly** - Smaller container images  
✅ **Cloud Ready** - Perfect for serverless/containers  

---

## ⚙️ Configuration Comparison

### DSN Formats (Both work!)

```python
# Format 1: Easy Connect
dsn = "host/service_name"           # Default port 1521
dsn = "host:1522/service_name"      # Custom port

# Format 2: TNS Name
dsn = "PROD_DB"                     # From tnsnames.ora

# Format 3: Full Connect String
dsn = """(DESCRIPTION=
            (ADDRESS=(PROTOCOL=TCP)(HOST=myhost)(PORT=1521))
            (CONNECT_DATA=(SERVICE_NAME=myservice)))"""
```

### Pool Configuration

```python
# Minimal
pool = oracledb.create_pool(
    user='user',
    password='pass',
    dsn='host/service'
)

# Full Options
pool = oracledb.create_pool(
    user='user',
    password='pass',
    dsn='host/service',
    min=2,                    # Minimum connections
    max=10,                   # Maximum connections
    increment=1,              # Connection increment
    threaded=True,            # Threading support
    events=True,              # Event handling
    getmode=oracledb.POOL_GETMODE_WAIT,  # Wait for connection
    timeout=30,               # Connection timeout
    wait_timeout=1000         # Pool wait timeout (ms)
)
```

---

## 🔄 Quick Migration Checklist

- [ ] Uninstall cx_Oracle
- [ ] Install python-oracledb 2.0.0
- [ ] Update `import cx_Oracle` → `import oracledb`
- [ ] Update `SessionPool()` → `create_pool()`
- [ ] Update `cursor.var(cx_Oracle.NUMBER)` → `cursor.var(int)`
- [ ] Update exception handling
- [ ] Test database connection
- [ ] Run test suite
- [ ] Update documentation
- [ ] Deploy!

---

**Migration is straightforward and provides significant benefits!** 🚀

The code changes are minimal, and you gain better performance, easier deployment, and future-proof compatibility.
