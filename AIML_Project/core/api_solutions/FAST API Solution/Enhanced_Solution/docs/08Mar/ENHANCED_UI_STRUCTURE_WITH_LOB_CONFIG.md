# 🏗️ Monitoring System - Enhanced UI Structure with LOB-Based Configuration

## 🎯 Your Requirements

1. **Main Page (Public)** - Health status dashboard per LOB
2. **LOB-Specific Tabs** - Different monitoring tools per LOB
3. **Delayed Authentication** - TOTP only when clicking "Access Monitoring"
4. **Permission-Based Access** - SQL writes restricted by role
5. **Configurable Views** - Show only allowed tabs per LOB

---

## 🏛️ Recommended Three-Section Architecture

```
┌─────────────────────────────────────────┐
│  SECTION 1: LANDING PAGE (Public)       │
│  - No authentication required            │
│  - Select LOB dropdown                   │
│  - Health Status Grid (read-only view)  │
│  - [View Details] [Access Monitoring]   │
└──────────┬──────────────────────────────┘
           │
    ┌──────┴─────────┐
    │                │
    ▼                ▼
┌──────────┐  ┌─────────────────┐
│ SECTION  │  │  LOGIN MODAL    │
│ 2: LOB   │  │  - Username     │
│ DETAILS  │  │  - Password     │
│ (Public) │  │  - TOTP Code    │
└──────────┘  └────────┬────────┘
                       │
                       ▼
              ┌─────────────────────┐
              │ SECTION 3:          │
              │ MONITORING TABS     │
              │ (Protected)         │
              │ - LOB-specific tabs │
              │ - Permission-based  │
              └─────────────────────┘
```

---

## 📊 LOB Configuration Database Schema

```sql
-- LOB Monitoring Configuration
CREATE TABLE LOB_MONITORING_CONFIG (
    CONFIG_ID NUMBER PRIMARY KEY,
    LOB_NAME VARCHAR2(100) NOT NULL,
    MONITORING_TYPE VARCHAR2(50) NOT NULL,
    IS_ENABLED CHAR(1) DEFAULT 'Y',
    DISPLAY_ORDER NUMBER,
    CREATED_DATE DATE DEFAULT SYSDATE,
    
    CONSTRAINT UQ_LOB_MONITOR UNIQUE (LOB_NAME, MONITORING_TYPE)
);

-- Sample Data
INSERT INTO LOB_MONITORING_CONFIG VALUES 
(1, 'Digital Technology', 'SQL_API', 'Y', 1, SYSDATE),
(2, 'Digital Technology', 'APPD', 'Y', 2, SYSDATE),
(3, 'Digital Technology', 'KIBANA', 'Y', 3, SYSDATE),
(4, 'Digital Technology', 'SPLUNK', 'Y', 4, SYSDATE),
(5, 'Digital Technology', 'AWR', 'Y', 5, SYSDATE),
(6, 'Digital Technology', 'PC_ANALYSIS', 'Y', 6, SYSDATE);

INSERT INTO LOB_MONITORING_CONFIG VALUES
(7, 'Payments', 'APPD', 'Y', 1, SYSDATE),
(8, 'Payments', 'KIBANA', 'Y', 2, SYSDATE);

INSERT INTO LOB_MONITORING_CONFIG VALUES
(9, 'Corporate', 'SQL_API', 'Y', 1, SYSDATE),
(10, 'Corporate', 'APPD', 'Y', 2, SYSDATE),
(11, 'Corporate', 'AWR', 'Y', 3, SYSDATE);

COMMIT;
```

---

## 🎨 Complete HTML Structure

See the complete index.html structure in the uploaded file.

**Key Sections:**
1. **Landing Page** - LOB selector + health grid (public)
2. **LOB Detail Page** - Detailed health metrics (public)
3. **Monitoring Dashboard** - Full tools (protected, requires login)
4. **Login Modal** - TOTP authentication overlay

---

## 🔄 User Flow

### Flow 1: View Health Status (No Auth)
```
1. User lands on page
2. Selects LOB from dropdown
3. Sees health status grid
4. Can click "View Details" for more info
5. Still no authentication required
```

### Flow 2: Access Monitoring Tools (Auth Required)
```
1. User clicks "Access Monitoring Tools"
2. Login modal appears
3. Enter username + password + TOTP
4. After successful login:
   - Show monitoring dashboard
   - Display LOB-specific tabs only
   - Show/hide features based on permissions
```

---

## 📋 LOB-to-Tools Mapping

```javascript
const LOB_MONITORING_MAP = {
    'Digital Technology': ['SQL_API', 'APPD', 'KIBANA', 'SPLUNK', 'AWR', 'PC_ANALYSIS'],
    'Payments': ['APPD', 'KIBANA'],
    'Corporate': ['SQL_API', 'APPD', 'AWR'],
    'Retail Banking': ['APPD', 'KIBANA', 'SPLUNK']
};
```

---

## 🔒 Permission-Based Features

### Viewer (read permission only):
```
✅ View health status
✅ View monitoring tabs
✅ View reports
❌ Upload data
❌ Register tests
❌ Delete records
```

### Performance Engineer (read + write + register_test):
```
✅ Everything viewers can do
✅ Upload AWR reports
✅ Register test runs
✅ Modify configurations
❌ Delete records
❌ Manage users
```

### Admin (all permissions):
```
✅ Everything
✅ Delete records
✅ Manage users
✅ Configure system
```

---

## 🎯 Implementation Phases

### Phase 1: Public Landing Page
- [x] LOB selector dropdown
- [x] Health status grid (dynamic based on LOB)
- [x] Action buttons (View Details, Access Monitoring)
- [x] No authentication required

### Phase 2: LOB Detail Page
- [x] Detailed health metrics
- [x] Still public access
- [x] Button to access monitoring tools

### Phase 3: Authentication
- [x] Login modal (overlay, not new page)
- [x] TOTP support
- [x] Session management
- [x] Permission loading

### Phase 4: Monitoring Dashboard
- [x] User header with logout
- [x] LOB-based tab filtering
- [x] Permission-based feature visibility
- [x] Actual monitoring content per tab

---

## 🔧 For Claude Copilot Agent

### Key Integration Points:

**1. Merge with Existing Code:**
```
- Copy HTML structure from SECTION 1-3
- Copy all JavaScript functions
- Update API_BASE constant
- Replace placeholder health checks with actual API calls
```

**2. Update API Endpoints:**
```
- Authentication: /api/v1/auth/login, /auth/me, /auth/logout
- Health Checks: /api/health/sql, /api/health/appd, etc.
- LOB Config: /api/lob/monitoring-config
```

**3. Customize for Company:**
```
- Update LOB names in LOB_MONITORING_MAP
- Update MONITORING_TOOLS metadata
- Add actual monitoring content in tabs
- Implement upload functionality
```

**4. Test Flow:**
```
1. Select LOB → See health grid
2. Click "View Details" → See detailed page
3. Click "Access Monitoring" → See login modal
4. Login → See monitoring dashboard with correct tabs
5. Check permission-based features show/hide correctly
```

---

## 📊 Benefits of This Architecture

✅ **Progressive Disclosure** - Show simple view first, detailed view on demand  
✅ **Delayed Authentication** - Only when needed for write operations  
✅ **LOB-Based Configuration** - Easy to add/remove monitoring tools per LOB  
✅ **Permission-Based UI** - Features automatically show/hide based on role  
✅ **Single Page App** - No page reloads, smooth transitions  
✅ **Responsive Design** - Works on desktop and tablet  

---

## 🚀 Next Steps

1. **Download** the complete HTML structure
2. **Update** API endpoints with your actual backend
3. **Test** on company machine with Copilot Agent
4. **Customize** LOB configurations for your needs
5. **Deploy** and enjoy! 🎉

**File ready for Copilot Agent integration!**




Additional Information
🎯 Your Solution: Three-Section Architecture
Section 1: Landing Page (Public - No Auth)
- LOB Selector dropdown
- Health Status Grid (Digital Tech: 6 tools, Payments: 2 tools)
- Read-only view
- Buttons: [View Details] [Access Monitoring]
Section 2: LOB Detail Page (Public - No Auth)
- Detailed health metrics for selected LOB
- Still no authentication
- Button: [Access Monitoring Tools] → Triggers login
Section 3: Monitoring Dashboard (Protected - Requires TOTP)
- Appears ONLY after successful login
- Shows LOB-specific tabs (filtered by LOB config)
- Permission-based features:
  • Viewers: Read-only
  • Engineers: Can upload data
  • Admins: Full access

📊 LOB Configuration
Database-Driven Config:
sql-- Each LOB has its own monitoring tools
Digital Technology: SQL_API, AppD, Kibana, Splunk, AWR, PC
Payments: AppD, Kibana
Corporate: SQL_API, AppD, AWR
JavaScript Map:
javascriptconst LOB_MONITORING_MAP = {
    'Digital Technology': ['SQL_API', 'APPD', 'KIBANA', 'SPLUNK', 'AWR', 'PC_ANALYSIS'],
    'Payments': ['APPD', 'KIBANA'],
    'Corporate': ['SQL_API', 'APPD', 'AWR']
};
```

---

## 🔄 **User Flow**

### **View Health (No Login):**
```
1. Select LOB → See health grid
2. Click "View Details" → See detailed metrics
3. All public, no authentication yet
```

### **Access Monitoring (Login Required):**
```
1. Click "Access Monitoring Tools"
2. Login modal appears (TOTP)
3. After login → Monitoring dashboard
4. Only LOB-allowed tabs visible
5. Features shown/hidden by permissions
PAT token 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