# 🚀 AWR Analysis & Performance Center - Quick Start Guide

## 📦 What You Get

Complete implementation for:
1. **AWR Report Analysis** - Upload HTML reports, get performance concerns
2. **Performance Center Integration** - Fetch LoadRunner test results
3. **Unified RUN_ID System** - Links all monitoring solutions

---

## 📚 Implementation Files

### Part 1: Database & Models
- **Database Schema** (8 tables)
  - `RUN_MASTER` - Central run registry
  - `AWR_ANALYSIS_RESULTS` - Analysis summary
  - `AWR_CONCERNS` - Performance issues
  - `AWR_TOP_SQL` - Slow queries
  - `AWR_WAIT_EVENTS` - Wait event stats
  - `PC_TEST_RUNS` - Performance Center runs
  - `LR_TRANSACTION_RESULTS` - LoadRunner transactions
  - Updates to `APPD_MONITORING_RUNS`

- **Run ID Generator** (`common/run_id_generator.py`)
- **Pydantic Models** (`monitoring/awr/models.py`)

### Part 2: AWR Parser & Analyzer
- **AWR Parser** (`monitoring/awr/parser.py`) - Extracts data from HTML
- **AWR Analyzer** (`monitoring/awr/analyzer.py`) - Identifies concerns

### Part 3: Database & API
- **Database Operations** (`monitoring/awr/database.py`)
- **API Routes** (`monitoring/awr/routes.py`)

---

## 🔧 Run ID Format

### Master Run ID
```
Format: RUNID_{PC_RUN_ID}_{DATE}_{SEQ}
Example: RUNID_35678_04Mar2026_001
```

### Solution-Specific IDs
```
AppD: AppD_Run_04Mar2026_001_35678
AWR: AWR_Run_04Mar2026_001_35678
PC: PC_Run_04Mar2026_001_35678
Mongo: Mongo_Run_04Mar2026_001_35678
```

---

## 📊 Implementation Steps

### Step 1: Create Database Tables (10 min)
Run all SQL from Part 1:
- RUN_MASTER
- AWR_ANALYSIS_RESULTS
- AWR_CONCERNS
- AWR_TOP_SQL
- AWR_WAIT_EVENTS
- PC_TEST_RUNS
- LR_TRANSACTION_RESULTS
- ALTER APPD_MONITORING_RUNS

### Step 2: Add Run ID Generator (5 min)
Create `common/run_id_generator.py` with `RunIDGenerator` class

### Step 3: Create AWR Module (30 min)
```
monitoring/awr/
├── __init__.py
├── models.py          # Pydantic models
├── parser.py          # AWR HTML parser
├── analyzer.py        # Performance analyzer
├── database.py        # Database operations
└── routes.py          # API endpoints
```

### Step 4: Update AppD Monitoring (10 min)
Add RUN_ID and PC_RUN_ID to AppD monitoring start:
```python
# When starting AppD monitoring
run_id = RunIDGenerator.generate_master_run_id(pc_run_id, sequence)
appd_run_id = RunIDGenerator.generate_solution_run_id("AppD", pc_run_id, sequence)

# Save to APPD_MONITORING_RUNS with both IDs
```

### Step 5: Test AWR Upload (15 min)
```bash
# Upload AWR report
curl -X POST http://localhost:8000/api/v1/awr/upload \
  -F "file=@awr_report.html" \
  -F "run_id=RUNID_35678_04Mar2026_001" \
  -F "pc_run_id=35678" \
  -F "database_name=PRODDB" \
  -F "lob_name=Digital Technology"
```

---

## 🎯 Key Features

### AWR Analysis
✅ Parses Oracle AWR HTML reports
✅ Identifies performance concerns automatically
✅ Categorizes by severity (CRITICAL, WARNING, INFO)
✅ Analyzes:
- Instance efficiency (Buffer cache, Library cache, Soft parse)
- Top SQL statements (Slow queries, High CPU, High I/O)
- Wait events (I/O waits, Latch contention, Locks)
- System statistics
- Time model statistics

### Concern Detection
- **CRITICAL**: Hard parsing, very slow SQL, high wait times
- **WARNING**: Low hit ratios, moderate performance issues
- **INFO**: Minor optimizations, recommendations

### Run ID Linking
- All monitoring solutions share same PC_RUN_ID
- Easy cross-solution correlation
- Unified reporting across tools

---

## 📋 API Endpoints

### AWR Analysis
```
POST /api/v1/awr/upload
- Upload AWR HTML report
- Returns: Analysis summary with concerns

GET /api/v1/awr/analysis/{run_id}
- Get analysis for specific run
- Returns: Full analysis with all concerns

GET /api/v1/awr/health/{lob_name}
- Get AWR status for LOB (for landing page)
```

### Performance Center (To be implemented)
```
POST /api/v1/pc/fetch-results
- Fetch results from Performance Center
- Parse summary.html
- Extract LoadRunner transactions

GET /api/v1/pc/results/{run_id}
- Get LR transaction results
```

---

## 🔍 Example Usage

### 1. Upload AWR Report
```python
import requests

files = {'file': open('awr_report.html', 'rb')}
data = {
    'run_id': 'RUNID_35678_04Mar2026_001',
    'pc_run_id': '35678',
    'database_name': 'PRODDB',
    'lob_name': 'Digital Technology',
    'track': 'CDV3',
    'test_name': 'Peak Load Test'
}

response = requests.post(
    'http://localhost:8000/api/v1/awr/upload',
    files=files,
    data=data
)

result = response.json()
print(f"Analysis ID: {result['analysis_id']}")
print(f"Total Concerns: {result['total_concerns']}")
print(f"Critical: {result['critical_concerns']}")
```

### 2. Get Analysis Results
```python
run_id = 'RUNID_35678_04Mar2026_001'
response = requests.get(f'http://localhost:8000/api/v1/awr/analysis/{run_id}')

data = response.json()
for concern in data['concerns']:
    print(f"{concern['severity']}: {concern['title']}")
    print(f"  {concern['recommendation']}")
```

### 3. Generate Run IDs
```python
from common.run_id_generator import RunIDGenerator

pc_run_id = "35678"

# Master run ID
master = RunIDGenerator.generate_master_run_id(pc_run_id, 1)
# RUNID_35678_04Mar2026_001

# AppD run ID
appd = RunIDGenerator.generate_solution_run_id("AppD", pc_run_id, 1)
# AppD_Run_04Mar2026_001_35678

# AWR run ID
awr = RunIDGenerator.generate_solution_run_id("AWR", pc_run_id, 1)
# AWR_Run_04Mar2026_001_35678
```

---

## 🎨 UI Integration (Incremental Changes Coming)

### AWR Tab in index.html
Will show:
- Upload AWR report form
- Analysis results display
- Concerns categorized by severity
- Top SQL statements
- Wait events visualization
- Recommendations

### Landing Page
Will show AWR status:
- Recent analyses count
- Current status (configured/not configured)
- LOB-specific analysis summary

---

## 📊 Sample Analysis Output

```json
{
  "success": true,
  "awr_run_id": "AWR_Run_04Mar2026_001_35678",
  "run_id": "RUNID_35678_04Mar2026_001",
  "analysis_id": 1,
  "database_name": "PRODDB",
  "instance_name": "PROD1",
  "snapshot_begin": 12345,
  "snapshot_end": 12346,
  "total_concerns": 8,
  "critical_concerns": 2,
  "warning_concerns": 5,
  "info_concerns": 1,
  "concerns": [
    {
      "category": "INSTANCE_EFFICIENCY",
      "severity": "CRITICAL",
      "title": "Excessive Hard Parsing Detected",
      "description": "Soft parse ratio is only 45.2%",
      "recommendation": "URGENT: Use bind variables..."
    },
    {
      "category": "TOP_SQL",
      "severity": "CRITICAL",
      "title": "Slow SQL Statement: abc123xyz",
      "description": "SQL takes 5,234ms per execution",
      "recommendation": "Review execution plan..."
    }
  ]
}
```

---

## ✅ Next Steps

1. **Implement Performance Center Integration** (Part 4)
   - PC connection API
   - Summary.html parser
   - LR transaction extraction

2. **Create UI Components**
   - AWR upload form
   - Results visualization
   - Concerns dashboard

3. **Add Cross-Solution Reports**
   - Unified dashboard showing all monitoring
   - Correlation between AppD, AWR, LR results
   - Performance trending

---

## 🐛 Troubleshooting

### Issue: AWR parsing fails
**Solution**: Check HTML structure. AWR reports vary by version. Parser handles common formats.

### Issue: Database constraint violation
**Solution**: Ensure RUN_MASTER entry exists before inserting AWR analysis.

### Issue: Run ID conflicts
**Solution**: Use `get_next_sequence()` to auto-increment sequence number.

---

**Total Implementation Time**: ~2-3 hours
**Difficulty**: Medium-Advanced
**Files Created**: ~10 Python files, 8 database tables

Ready to implement! 🚀