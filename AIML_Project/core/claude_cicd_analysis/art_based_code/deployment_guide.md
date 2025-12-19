# Complete Deployment Guide - CI/CD NFT Test Analysis System

## 📋 Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Production Deployment](#production-deployment)
3. [Security Configuration](#security-configuration)
4. [Performance Optimization](#performance-optimization)
5. [Monitoring & Maintenance](#monitoring--maintenance)

---

# Local Development Setup

## Prerequisites

### System Requirements
- **Operating System:** Windows 10+, Linux (Ubuntu 20.04+), or macOS 10.15+
- **Python:** 3.8 or higher
- **Memory:** Minimum 4GB RAM
- **Disk Space:** 2GB free space
- **Network:** Access to Oracle database

### Software Requirements
- Python 3.8+
- Oracle Instant Client
- Git (optional, for version control)
- Web browser (Chrome, Firefox, Edge, Safari)

---

## Step 1: Install Python

### Windows:
```bash
# Download from python.org
# During installation, check "Add Python to PATH"
python --version
```

### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
```

### macOS:
```bash
brew install python3
python3 --version
```

---

## Step 2: Install Oracle Instant Client

### Windows:
```
1. Download Oracle Instant Client Basic from:
   https://www.oracle.com/database/technologies/instant-client/downloads.html

2. Extract to: C:\oracle\instantclient_21_1

3. Add to System PATH:
   - Right-click "This PC" → Properties
   - Advanced system settings → Environment Variables
   - Edit PATH, add: C:\oracle\instantclient_21_1
   
4. Restart Command Prompt
```

### Linux:
```bash
# Download Instant Client
cd /tmp
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-21.1.0.0.0.zip

# Extract
sudo mkdir -p /opt/oracle
sudo unzip instantclient-basic-linux.x64-21.1.0.0.0.zip -d /opt/oracle

# Set environment variables
echo 'export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH' >> ~/.bashrc
echo 'export ORACLE_HOME=/opt/oracle/instantclient_21_1' >> ~/.bashrc
source ~/.bashrc

# Install dependencies
sudo apt-get install libaio1
```

### macOS:
```bash
# Install via Homebrew
brew tap InstantClientTap/instantclient
brew install instantclient-basic

# Or manually download and extract
# Set environment in ~/.zshrc or ~/.bash_profile
export ORACLE_HOME=/usr/local/oracle/instantclient_21_1
export LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH
```

---

## Step 3: Project Setup

### Create Project Directory
```bash
# Create project folder
mkdir cicd-analytics
cd cicd-analytics

# Create subdirectories
mkdir logs
mkdir backups
```

### Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Your prompt should now show (venv)
```

### Create requirements.txt
```bash
# Create requirements.txt file with this content:
cat > requirements.txt << EOF
cx_Oracle==8.3.0
pandas==2.1.3
numpy==1.24.3
Flask==3.0.0
flask-cors==4.0.0
scikit-learn==1.3.2
python-dateutil==2.8.2
pytz==2023.3
EOF
```

### Install Dependencies
```bash
# Install all packages
pip install -r requirements.txt

# Verify installation
pip list

# You should see all packages listed
```

---

## Step 4: Database Configuration

### Test Oracle Connection
```python
# Create test_connection.py
import cx_Oracle

# Replace with your credentials
username = "your_username"
password = "your_password"
dsn = "hostname:1521/servicename"

try:
    connection = cx_Oracle.connect(username, password, dsn)
    print("✓ Successfully connected to Oracle Database")
    
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM DUAL")
    result = cursor.fetchone()
    print(f"✓ Query executed successfully: {result}")
    
    cursor.close()
    connection.close()
    print("✓ Connection closed")
    
except cx_Oracle.DatabaseError as e:
    error, = e.args
    print(f"✗ Database error: {error.code} - {error.message}")
except Exception as e:
    print(f"✗ Error: {str(e)}")
```

Run the test:
```bash
python test_connection.py
```

### Setup Database Table and Sample Data

**Option 1: Run SQL Script**
```bash
# If you have sqlplus installed
sqlplus username/password@//hostname:1521/servicename @sample_data_generator.sql
```

**Option 2: Use SQL Developer or other GUI tool**
- Copy the SQL from sample_data_generator.sql
- Execute in your SQL client

### Verify Data
```sql
-- Check if data was created
SELECT COUNT(*) as total_records,
       MIN(TEST_DATE) as earliest,
       MAX(TEST_DATE) as latest
FROM PTE_TABLE;

-- Should return 30+ days of data
```

---

## Step 5: Configure Application

### Update Database Credentials in app.py

```python
# Edit lines 17-21 in app.py
DB_CONFIG = {
    'user': 'your_actual_username',
    'password': 'your_actual_password',
    'dsn': 'your_host:1521/your_service_name'
}

# Example:
DB_CONFIG = {
    'user': 'cicd_user',
    'password': 'SecurePass123',
    'dsn': 'db.company.com:1521/PROD'
}
```

### Create Environment Variables (Better Security)

**Create .env file:**
```bash
# .env (DO NOT commit to git!)
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password
ORACLE_DSN=hostname:1521/servicename
FLASK_ENV=development
```

**Update app.py to use .env:**
```python
# Add at top of app.py
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'user