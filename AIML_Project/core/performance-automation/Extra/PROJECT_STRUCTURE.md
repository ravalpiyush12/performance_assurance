# Project Structure

## Directory Layout

```
performance-automation/
│
├── Jenkinsfile                      # Main pipeline script (COPY TO JENKINS)
├── README.md                        # Complete documentation
├── QUICKSTART.md                    # 5-minute setup guide
├── TESTING.md                       # Testing guide & examples
├── config.ini                       # Configuration template
├── setup.sh                         # Quick setup script
│
└── scripts/
    ├── pc_automation.py            # PC API client
    ├── results_analyzer.py         # Results parser & reporter
    └── requirements.txt            # Python dependencies
```

## File Descriptions

### Root Files

#### `Jenkinsfile` (⭐ MOST IMPORTANT)
- **Purpose**: Complete Jenkins pipeline definition
- **Size**: ~450 lines
- **Action**: Copy entire content to Jenkins Pipeline script
- **Contains**:
  - All pipeline stages
  - Parameter definitions
  - Email templates
  - Error handling
  - Post-build actions

#### `README.md`
- **Purpose**: Complete project documentation
- **Contains**:
  - Architecture overview
  - Prerequisites
  - Detailed setup instructions
  - Configuration guide
  - Troubleshooting
  - Best practices

#### `QUICKSTART.md`
- **Purpose**: Get started in 5 minutes
- **Contains**:
  - Step-by-step checklist
  - Quick reference
  - Common issues & fixes
  - Success indicators

#### `TESTING.md`
- **Purpose**: Testing guide and examples
- **Contains**:
  - Test scenarios
  - Validation steps
  - Debugging checklist
  - Performance benchmarks
  - Maintenance tasks

#### `config.ini`
- **Purpose**: Configuration template
- **Use**: Reference for customization
- **Contains**:
  - Server settings
  - SLA thresholds
  - Email settings
  - Advanced options

#### `setup.sh`
- **Purpose**: Automated setup script
- **Use**: Run once to setup environment
- **Actions**:
  - Checks prerequisites
  - Installs dependencies
  - Creates directories
  - Validates scripts

### Scripts Directory

#### `pc_automation.py`
- **Purpose**: Performance Center API automation
- **Size**: ~350 lines
- **Language**: Python 3.7+
- **Functions**:
  - `trigger` - Start PC test
  - `monitor` - Track test progress
  - `download` - Retrieve results
- **Dependencies**: requests, urllib3

#### `results_analyzer.py`
- **Purpose**: Results parsing and reporting
- **Size**: ~450 lines
- **Language**: Python 3.7+
- **Functions**:
  - `analyze` - Process results
  - `report` - Generate HTML/Excel
- **Dependencies**: pandas, openpyxl

#### `requirements.txt`
- **Purpose**: Python package dependencies
- **Packages**:
  - requests (API calls)
  - pandas (data processing)
  - openpyxl (Excel generation)
  - urllib3 (HTTP handling)

## File Sizes (Approximate)

```
Jenkinsfile           15 KB
README.md             25 KB
QUICKSTART.md          8 KB
TESTING.md            12 KB
config.ini             1 KB
setup.sh               3 KB
pc_automation.py      12 KB
results_analyzer.py   15 KB
requirements.txt     100 bytes
```

## How Files Work Together

### Execution Flow

```
1. JENKINS reads Jenkinsfile
   └─> Defines pipeline stages
   └─> Sets up parameters
   └─> Configures environment

2. PIPELINE calls setup.sh (optional)
   └─> Checks Python
   └─> Installs dependencies
   └─> Creates directories

3. PIPELINE calls pc_automation.py
   └─> trigger command
       └─> Authenticates with PC
       └─> Starts test
       └─> Returns run_id
   
   └─> monitor command
       └─> Polls for status
       └─> Waits for completion
       └─> Returns final status
   
   └─> download command
       └─> Downloads results
       └─> Saves to results/

4. PIPELINE calls results_analyzer.py
   └─> analyze command
       └─> Parses metadata
       └─> Generates statistics
       └─> Creates JSON summary
   
   └─> report command
       └─> Creates HTML report
       └─> Creates Excel report
       └─> Formats for display

5. JENKINS publishes results
   └─> HTML Report viewer
   └─> Artifact archival
   └─> Email notification
```

## Dependencies Between Files

```
Jenkinsfile
    ├─> Requires: pc_automation.py
    ├─> Requires: results_analyzer.py
    ├─> Requires: requirements.txt (indirectly)
    └─> References: config.ini (for default values)

pc_automation.py
    ├─> Requires: requests
    └─> Requires: urllib3

results_analyzer.py
    ├─> Requires: pandas
    └─> Requires: openpyxl

setup.sh
    └─> Requires: requirements.txt
```

## Customization Points

### Easy Customizations (No coding)

1. **Jenkinsfile Parameters** (Lines 8-48)
   - Default PC server
   - Default domain/project
   - Default email recipients

2. **config.ini** (All sections)
   - SLA thresholds
   - Timeouts
   - Email settings

### Medium Customizations (Basic coding)

1. **results_analyzer.py**
   - Transaction names (Line ~90)
   - SLA definitions (Line ~110)
   - Report styling (Line ~180)

2. **Email template in Jenkinsfile** (Line ~290)
   - HTML structure
   - Colors and styling
   - Additional fields

### Advanced Customizations (Full coding)

1. **pc_automation.py**
   - API endpoints
   - Authentication method
   - Error handling
   - Retry logic

2. **results_analyzer.py**
   - Data parsing logic
   - Statistical calculations
   - Chart generation
   - Export formats

## What to Modify First

### For Your Environment

1. **Jenkinsfile** - Lines 8-18, 43
   ```groovy
   defaultValue: 'your-pc-server.com'
   defaultValue: 'YOUR_DOMAIN'
   defaultValue: 'YOUR_PROJECT'
   ```

2. **pc_automation.py** - Line 20
   ```python
   self.base_url = f"http://{server}/LoadTest/rest"
   # Change if your PC uses different URL structure
   ```

### For Your Tests

1. **results_analyzer.py** - Line 85-130
   ```python
   # Update transaction names to match your tests
   self.transactions = [...]
   
   # Update SLAs to match your requirements
   self.sla_results = [...]
   ```

## Generated Files (Runtime)

These files are created when pipeline runs:

```
results/
├── run_info.json              # From: trigger stage
├── execution_log.json         # From: monitor stage
├── metadata_{run_id}.json     # From: download stage
├── report_{run_id}.html       # From: download stage
├── results_{run_id}.zip       # From: download stage
├── analysis_summary.json      # From: analyze stage
├── performance_data.xlsx      # From: analyze stage
├── performance_report.html    # From: analyze stage
└── final_report.html         # From: report stage
```

## Version Control Recommendations

### Files to Commit to Git

```
✓ Jenkinsfile
✓ README.md
✓ QUICKSTART.md
✓ TESTING.md
✓ config.ini
✓ setup.sh
✓ scripts/pc_automation.py
✓ scripts/results_analyzer.py
✓ scripts/requirements.txt
✓ .gitignore
```

### Files to Ignore (.gitignore)

```
# Results and temporary files
results/
logs/
*.pyc
__pycache__/
.pytest_cache/

# Environment
venv/
.env
*.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

## Deployment Options

### Option 1: Copy-Paste (Quickest)
1. Copy Jenkinsfile to Jenkins UI
2. Scripts are created in workspace
3. No Git repository needed

### Option 2: Git Repository (Recommended)
1. Commit all files to Git
2. Configure Jenkins to use SCM
3. Jenkinsfile path: `Jenkinsfile`

### Option 3: Shared Library (Advanced)
1. Convert to Jenkins Shared Library
2. Store in separate repository
3. Reference in multiple pipelines

## Backup Strategy

**What to backup:**
- All source files (scripts, Jenkinsfile)
- Configuration (config.ini)
- Documentation (all .md files)

**What NOT to backup:**
- results/ directory
- Temporary files
- Log files

**Backup frequency:**
- Source files: After each change
- Configuration: Weekly
- Documentation: After updates

---

## Quick Reference Card

| File | Size | Must Edit? | Purpose |
|------|------|-----------|---------|
| Jenkinsfile | 15KB | ✅ YES | Pipeline definition |
| pc_automation.py | 12KB | ⚠️ Maybe | API integration |
| results_analyzer.py | 15KB | ⚠️ Maybe | Results parsing |
| requirements.txt | 100B | ❌ No | Dependencies |
| config.ini | 1KB | ✅ YES | Configuration |
| README.md | 25KB | ❌ No | Documentation |
| QUICKSTART.md | 8KB | ❌ No | Setup guide |
| TESTING.md | 12KB | ❌ No | Test guide |
| setup.sh | 3KB | ❌ No | Setup script |

Legend:
- ✅ YES = Must customize for your environment
- ⚠️ Maybe = Customize for advanced features
- ❌ No = Use as-is

---

**Need help? Check README.md for detailed documentation!**
