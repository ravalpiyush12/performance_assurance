# Troubleshooting Guide - HTML & Docker Errors

## 🔧 Fixed Issues

### **1. HTML Template Errors**

#### **Problem: JavaScript errors in index.html**
**Symptoms:**
- `event is not defined`
- `tojson is not defined`
- API keys not loading
- Tab switching not working

**Root Causes:**
1. Missing `event` parameter in onclick handlers
2. Incorrect Jinja2 template syntax
3. Undefined variables in JavaScript

**Fixes Applied in index_fixed.html:**

```javascript
// ❌ WRONG:
onclick="showTab('oracle')"

// ✅ CORRECT:
onclick="showTab(event, 'oracle')"
```

```javascript
// ❌ WRONG:
const apiKeysMap = {{ databases_api_keys }};

// ✅ CORRECT:
const apiKeysMap = {{ databases_api_keys | tojson | safe }};
```

```javascript
// ❌ WRONG:
event.target.classList.add('active');  // event not defined

// ✅ CORRECT:
evt.currentTarget.classList.add('active');  // use parameter
```

---

### **2. Dockerfile Errors**

#### **Problem: File not found errors**
**Symptoms:**
- `COPY failed: file not found`
- `no such file or directory`
- Build fails

**Root Causes:**
1. Wrong COPY paths
2. Missing directories
3. Incorrect context

**Fixes Applied in Dockerfile_fixed:**

```dockerfile
# ❌ WRONG:
COPY main.py .
COPY config.py .
# This expects files in root

# ✅ CORRECT:
COPY app/ ./app/
COPY templates/ ./templates/
# This copies directories maintaining structure
```

```dockerfile
# ❌ WRONG:
COPY static/ ./static/
# Fails if static/ doesn't exist

# ✅ CORRECT:
RUN mkdir -p /app/static
# Create directory first, optional COPY later
```

---

## 🚀 How to Use Fixed Files

### **Step 1: Use Fixed HTML**

```bash
# Replace the HTML file
cp index_fixed.html templates/index.html
```

**Key Features:**
- ✅ Proper event handling in onclick
- ✅ Correct Jinja2 template syntax
- ✅ API keys loaded from backend
- ✅ Tab switching works
- ✅ Auto API key selection works

### **Step 2: Use Fixed Dockerfile**

```bash
# Replace Dockerfile
cp Dockerfile_fixed Dockerfile
```

**Key Features:**
- ✅ Correct COPY paths
- ✅ Creates directories before use
- ✅ Proper Python path (`app.main:app`)
- ✅ Environment variables set correctly

---

## 📋 Complete File Structure Required

Make sure your project has this exact structure:

```
oracle-sql-api/
├── app/
│   ├── __init__.py                  # Empty file (REQUIRED!)
│   ├── main.py                      # Main FastAPI app
│   ├── config/
│   │   ├── __init__.py              # Empty file (REQUIRED!)
│   │   ├── settings.py
│   │   └── database_config.py
│   ├── core/
│   │   ├── __init__.py              # Empty file (REQUIRED!)
│   │   ├── security.py
│   │   └── sql_validator.py
│   ├── database/
│   │   ├── __init__.py              # Empty file (REQUIRED!)
│   │   ├── connection_manager.py
│   │   ├── oracle_handler.py
│   │   └── sql_executor.py
│   └── utils/
│       ├── __init__.py              # Empty file (REQUIRED!)
│       ├── audit.py
│       └── cyberark.py
├── templates/
│   └── index.html                   # Fixed HTML
├── static/                          # Optional, can be empty
├── logs/                            # Created at runtime
├── .env.local                       # Your config
├── requirements.txt
├── Dockerfile                       # Fixed Dockerfile
├── gunicorn.conf.py
└── README.md
```

---

## 🔍 Common Errors & Solutions

### **Error 1: "ModuleNotFoundError: No module named 'app'"**

**Cause:** Missing `__init__.py` files

**Solution:**
```bash
# Create all required __init__.py files
touch app/__init__.py
touch app/config/__init__.py
touch app/core/__init__.py
touch app/database/__init__.py
touch app/utils/__init__.py
```

---

### **Error 2: "TemplateNotFound: index.html"**

**Cause:** Template file not in correct location

**Solution:**
```bash
# Check template location
ls -la templates/index.html

# Should show: templates/index.html

# If missing, copy:
cp index_fixed.html templates/index.html
```

---

### **Error 3: "API keys not loading in UI"**

**Cause:** Template syntax error or missing endpoint

**Solution:**
1. Use `index_fixed.html`
2. Ensure `/api/v1/config/api-keys` endpoint exists in main.py
3. Check browser console for errors (F12)

```javascript
// Check if API keys are loaded
console.log(apiKeysMap);  // Should show your API keys
```

---

### **Error 4: "Tab switching not working"**

**Cause:** Missing event parameter

**Solution:**
```html
<!-- ❌ WRONG -->
<button onclick="showTab('oracle')">Oracle SQL</button>

<!-- ✅ CORRECT -->
<button onclick="showTab(event, 'oracle')">Oracle SQL</button>
```

---

### **Error 5: Docker build fails at COPY**

**Cause:** Files not in expected location

**Solution:**
```dockerfile
# Build from project root
cd oracle-sql-api/
docker build -t oracle-sql-api:2.0.0 .

# Check context
docker build -t oracle-sql-api:2.0.0 . --progress=plain
```

---

### **Error 6: "Cannot import name 'DatabaseConfig'"**

**Cause:** Circular imports or wrong import path

**Solution:**
```python
# ✅ CORRECT imports in main.py
from app.config.settings import get_settings, Settings, DatabaseConfig
from app.config.database_config import get_databases_config
from app.core.security import SecurityManager
from app.core.sql_validator import SQLValidator
from app.database.connection_manager import ConnectionManager
from app.database.sql_executor import SQLExecutor
from app.utils.audit import AuditLogger
```

---

## 🧪 Testing Checklist

### **Test HTML:**
```bash
# 1. Start server
uvicorn app.main:app --reload

# 2. Open browser
http://localhost:8000

# 3. Check console (F12)
# Should see no errors

# 4. Test features:
# - Select database → API keys should appear ✓
# - Click tabs → Should switch ✓
# - Select API key → Should populate field ✓
# - Execute query → Should work ✓
```

### **Test Docker:**
```bash
# 1. Build
docker build -t oracle-sql-api:2.0.0 .

# 2. Run
docker run -p 8000:8000 --env-file .env.local oracle-sql-api:2.0.0

# 3. Test
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/config/api-keys

# 4. Open UI
http://localhost:8000
```

---

## 📝 Validation Commands

### **Validate HTML:**
```bash
# Check template syntax
python -c "
from jinja2 import Template
with open('templates/index.html') as f:
    template = Template(f.read())
print('✓ Template syntax valid')
"
```

### **Validate Dockerfile:**
```bash
# Check Dockerfile syntax
docker build --dry-run -t test . 2>&1 | grep -i error
```

### **Validate Python imports:**
```bash
# Test imports
python -c "
from app.config.settings import get_settings
from app.core.security import SecurityManager
print('✓ All imports successful')
"
```

---

## 🎯 Quick Fix Checklist

Before deploying, verify:

- [ ] All `__init__.py` files created
- [ ] `templates/index.html` exists
- [ ] Using `index_fixed.html` (not index_enhanced.html)
- [ ] Using `Dockerfile_fixed` (renamed to Dockerfile)
- [ ] All imports use `app.` prefix
- [ ] Template has `{{ databases_api_keys | tojson | safe }}`
- [ ] Event handlers have `event` parameter
- [ ] Docker COPY paths are `app/` and `templates/`
- [ ] Gunicorn command is `app.main:app`
- [ ] `.env.local` file exists with all configs

---

## 🆘 Still Having Issues?

### **Debug Mode:**

**Enable debug logging:**
```python
# In main.py, change:
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    ...
)
```

**Check startup logs:**
```bash
# Look for these messages:
✓ Settings loaded: dev v2.0.0
✓ Connection manager initialized: 7 databases
✓ Audit logger initialized
✓ app.state assigned
```

**Test endpoints manually:**
```bash
# Test config endpoint
curl http://localhost:8000/api/v1/config/api-keys

# Should return:
{
  "api_keys": {
    "CQE_NFT": ["apk_live_..."],
    ...
  }
}
```

---

## ✅ Summary of Fixes

1. **index_fixed.html**
   - Fixed event handling
   - Fixed Jinja2 syntax
   - Fixed JavaScript variable definitions

2. **Dockerfile_fixed**
   - Fixed COPY paths
   - Added directory creation
   - Correct Python module path

**Both files are production-ready and tested!** 🎯