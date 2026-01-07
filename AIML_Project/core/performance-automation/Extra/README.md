# Performance Center - Jenkins Automation POC

Complete automation solution for triggering Performance Center load tests via Jenkins and automatically analyzing results.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Jenkins Configuration](#jenkins-configuration)
- [Usage](#usage)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This POC provides end-to-end automation for:
1. ✅ Triggering Performance Center tests from Jenkins
2. ✅ Monitoring test execution with real-time status updates
3. ✅ Downloading test results automatically
4. ✅ Analyzing results and generating comprehensive reports
5. ✅ Publishing reports to Jenkins and sending email notifications
6. ✅ SLA-based build status (Pass/Fail/Unstable)

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Jenkins   │─────>│  PC Automation   │─────>│  Performance    │
│   Pipeline  │      │     Scripts      │      │     Center      │
└─────────────┘      └──────────────────┘      └─────────────────┘
       │                      │                         │
       │                      │                         │
       ▼                      ▼                         ▼
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Reports   │◄─────│  Results         │◄─────│  Test Results   │
│  Dashboard  │      │  Analyzer        │      │   & Analysis    │
└─────────────┘      └──────────────────┘      └─────────────────┘
```

## 📦 Prerequisites

### Jenkins Server
- Jenkins 2.300+
- Required Plugins:
  - Pipeline
  - Credentials Binding
  - Email Extension
  - HTML Publisher
  - Git (if using SCM)

### Python Environment
- Python 3.7+
- pip

### Performance Center
- Performance Center 12.x or higher
- REST API enabled
- User account with test execution permissions

## 🚀 Setup Instructions

### Step 1: Prepare Jenkins Credentials

1. Go to Jenkins → Manage Jenkins → Manage Credentials
2. Add new credential (Username with password):
   - **ID**: `pc-credentials`
   - **Username**: Your PC username
   - **Password**: Your PC password
   - **Description**: Performance Center Credentials

### Step 2: Create Jenkins Pipeline Job

1. Go to Jenkins → New Item
2. Enter name: `Performance-Center-Automation`
3. Select: **Pipeline**
4. Click **OK**

### Step 3: Configure Pipeline

In the Pipeline section:
- **Definition**: Select `Pipeline script`
- **Script**: Copy the entire content from `Jenkinsfile`

#### Alternative: Use SCM
If you store scripts in Git:
- **Definition**: Select `Pipeline script from SCM`
- **SCM**: Git
- **Repository URL**: Your Git repository
- **Script Path**: `Jenkinsfile`

### Step 4: Install Email Extension Plugin

1. Manage Jenkins → Manage Plugins → Available
2. Search for "Email Extension Plugin"
3. Install and restart Jenkins

Configure SMTP:
1. Manage Jenkins → Configure System
2. Find "Extended E-mail Notification"
3. Configure your SMTP server settings

### Step 5: Setup Python Scripts

#### Option A: Store in Git Repository
```bash
# Clone or create repository
mkdir performance-automation
cd performance-automation

# Copy scripts
cp /path/to/scripts/* ./scripts/
cp /path/to/Jenkinsfile ./

# Commit and push
git add .
git commit -m "Add PC automation scripts"
git push
```

#### Option B: Store in Jenkins Workspace
The scripts will be created automatically in the workspace when you run the pipeline for the first time.

## ⚙️ Jenkins Configuration

### Pipeline Parameters

The pipeline accepts these parameters (auto-configured):

| Parameter | Default | Description |
|-----------|---------|-------------|
| PC_SERVER | pc-server.example.com | Performance Center server URL |
| PC_DOMAIN | DEFAULT | PC Domain name |
| PC_PROJECT | MyProject | PC Project name |
| TEST_ID | 1 | Test ID to execute |
| TEST_DURATION | 1800 | Test duration (seconds) |
| POST_RUN_ACTION | COLLATE_AND_ANALYZE | Post-test action |
| POLL_INTERVAL | 60 | Status check interval |
| EMAIL_RECIPIENTS | team@example.com | Email recipients |

### First-Time Configuration

Before running the pipeline, update these parameters:

```groovy
// In Jenkinsfile, update default values:
parameters {
    string(
        name: 'PC_SERVER',
        defaultValue: 'your-pc-server.company.com',  // ← Update this
        ...
    )
    string(
        name: 'PC_DOMAIN',
        defaultValue: 'YOUR_DOMAIN',  // ← Update this
        ...
    )
    string(
        name: 'PC_PROJECT',
        defaultValue: 'YOUR_PROJECT',  // ← Update this
        ...
    )
}
```

## 🎮 Usage

### Running the Pipeline

#### Via Jenkins UI
1. Go to your pipeline job
2. Click **Build with Parameters**
3. Update parameters as needed:
   - Enter your PC Server address
   - Enter Test ID
   - Set desired duration
   - Update email recipients
4. Click **Build**

#### Example Configuration
```
PC_SERVER: pc.mycompany.com
PC_DOMAIN: DEFAULT
PC_PROJECT: LoadTest
TEST_ID: 5
TEST_DURATION: 3600
POST_RUN_ACTION: COLLATE_AND_ANALYZE
POLL_INTERVAL: 60
EMAIL_RECIPIENTS: qa-team@company.com,devops@company.com
```

### Monitoring Execution

The pipeline will:
1. **Setup** - Prepare environment (1-2 min)
2. **Trigger** - Start PC test (30 sec)
3. **Monitor** - Wait for test completion (varies by test duration)
4. **Download** - Retrieve results (2-5 min)
5. **Analyze** - Process data (1-2 min)
6. **Report** - Generate and publish (1 min)

You can monitor progress in:
- Jenkins console output
- Jenkins Blue Ocean UI (recommended)

### Viewing Results

After completion:

1. **Jenkins Dashboard**
   - HTML Report: Click "Performance Test Report" link
   - Artifacts: Click build → "Artifacts" link

2. **Email**
   - Check configured email addresses
   - HTML report with summary statistics

3. **Workspace Files**
   - Excel file: `results/performance_data.xlsx`
   - JSON file: `results/analysis_summary.json`

## 🔧 Customization

### Modify Results Analysis

Edit `scripts/results_analyzer.py`:

```python
def generate_mock_data(self):
    """Customize transaction names and SLAs"""
    self.transactions = [
        {
            'name': 'YourTransaction',  # ← Change this
            'count': 1000,
            ...
        }
    ]
    
    self.sla_results = [
        {
            'name': 'Your SLA',  # ← Add your SLAs
            ...
        }
    ]
```

### Integrate Real PC Data

Replace mock data with actual PC API calls:

```python
def parse_pc_results(self, results_file):
    """Parse actual Performance Center results"""
    # Parse PC XML/JSON results
    tree = ET.parse(results_file)
    # Extract transaction data
    # Extract SLA data
    # Return structured data
```

### Add Custom Notifications

In `Jenkinsfile`, add notification stages:

```groovy
stage('Slack Notification') {
    steps {
        slackSend(
            color: 'good',
            message: "Test completed: ${env.BUILD_URL}"
        )
    }
}

stage('Jira Update') {
    steps {
        // Update Jira ticket with results
    }
}
```

### Custom SLA Thresholds

Modify build status based on your criteria:

```groovy
if (env.AVG_RESPONSE_TIME > 2.0) {
    currentBuild.result = 'UNSTABLE'
    echo "Response time threshold exceeded"
}

if (env.FAILED_TRANSACTIONS > 100) {
    currentBuild.result = 'FAILURE'
    echo "Too many failed transactions"
}
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Authentication Failed
```
✗ Authentication failed: 401 Unauthorized
```
**Solution**:
- Verify PC credentials in Jenkins
- Check PC user has API access
- Ensure PC REST API is enabled

#### 2. Test Not Found
```
✗ Failed to trigger test: 404 Not Found
```
**Solution**:
- Verify TEST_ID is correct
- Check domain and project names
- Ensure test exists and is not archived

#### 3. Python Module Not Found
```
ModuleNotFoundError: No module named 'pandas'
```
**Solution**:
```bash
# On Jenkins slave/agent
pip3 install --user -r scripts/requirements.txt
```

#### 4. Timeout During Monitoring
```
✗ Timeout reached (18000s)
```
**Solution**:
- Increase timeout in pipeline:
```groovy
timeout(time: 8, unit: 'HOURS') {  // Increase from 5 to 8
```

#### 5. Email Not Sent
**Solution**:
- Configure SMTP in Jenkins
- Check Email Extension Plugin settings
- Verify email addresses are valid

### Debug Mode

Enable verbose logging:

```groovy
// Add to pipeline environment
environment {
    DEBUG = 'true'
}

// In Python scripts
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Connectivity

Test PC connection:
```bash
# From Jenkins machine
curl -X POST http://pc-server:8080/LoadTest/rest/authentication-point/authenticate \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'
```

## 📊 Sample Output

### Console Output
```
========================================
Performance Center Automation POC
========================================
Server: pc.company.com
Domain: DEFAULT
Project: LoadTest
Test ID: 5
Duration: 1800 seconds
========================================

✓ Authentication successful!
✓ Test triggered successfully!
  Run ID: 12345

[14:30:15] Check #1 (Elapsed: 0s)
  Status: RUNNING

[14:31:15] Check #2 (Elapsed: 60s)
  Status: RUNNING

✓ Test completed with status: FINISHED
  Total execution time: 1850 seconds (30.8 minutes)

✓ Results downloaded successfully!
✓ Analysis completed successfully!
✓ Email notification sent!

========================================
Pipeline Execution Summary
========================================
Build Number: 42
Status: SUCCESS
========================================
```

### Generated Reports

- **HTML Report**: Interactive dashboard with charts
- **Excel Report**: Detailed data in multiple sheets
- **JSON Summary**: Machine-readable results

## 📝 Best Practices

1. **Start Small**: Test with short duration tests first
2. **Version Control**: Store scripts in Git
3. **Parameterize**: Use Jenkins parameters for flexibility
4. **Monitor Resources**: Check Jenkins agent disk space
5. **Archive Results**: Keep historical data for trending
6. **Secure Credentials**: Never hardcode passwords
7. **Error Handling**: Add retry logic for network issues
8. **Documentation**: Keep README updated with changes

## 🆘 Support

### Resources
- Performance Center Documentation
- Jenkins Pipeline Documentation
- Python Requests Library Docs

### Contact
For issues or questions:
- Create ticket in Jira
- Email: devops@company.com
- Slack: #performance-testing

## 📄 License

Internal use only - Company Proprietary

## 🔄 Version History

- **v1.0** (2025-01-02): Initial POC release
  - Basic automation workflow
  - Mock data for demo
  - HTML/Excel reporting

---

**Happy Testing! 🚀**