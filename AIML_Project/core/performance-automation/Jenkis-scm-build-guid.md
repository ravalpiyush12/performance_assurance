# Jenkins Pipeline from SCM - Bitbucket Folder Setup Guide

## 📂 Scenario

Your repository structure:
```
my-bitbucket-repo/
├── src/
├── docs/
├── jenkins/
│   ├── Jenkinsfile-PC-Tests          ← Your Jenkinsfile here
│   ├── scripts/
│   │   ├── parse_pc_report.py
│   │   └── load_to_oracle.py
│   └── config/
└── README.md
```

You want Jenkins to use the Jenkinsfile from `jenkins/` folder, not root.

---

## ✅ Solution: Configure Script Path

### Step 1: Create Jenkins Job

1. **Jenkins Dashboard → New Item**
2. **Name:** PC-Automated-Tests
3. **Type:** Pipeline
4. **Click OK**

### Step 2: Configure Pipeline Settings

In the job configuration:

1. **Pipeline Section:**
   ```
   Definition: Pipeline script from SCM
   ```

2. **SCM:** Git

3. **Repository URL:**
   ```
   https://bitbucket.org/your-company/your-repo.git
   
   OR (SSH)
   
   git@bitbucket.org:your-company/your-repo.git
   ```

4. **Credentials:**
   - Click "Add" → Jenkins
   - Kind: Username with password (for HTTPS)
   - OR Kind: SSH Username with private key (for SSH)
   - Add your Bitbucket credentials

5. **Branches to build:**
   ```
   */main
   
   OR
   
   */master
   
   OR
   
   */develop  (your branch name)
   ```

6. **🔑 KEY SETTING - Script Path:**
   ```
   jenkins/Jenkinsfile-PC-Tests
   ```
   
   **This tells Jenkins where to find your Jenkinsfile!**

7. **Additional Behaviours (Optional):**
   - Click "Add" → "Sparse Checkout paths"
   - Path: `jenkins/` (only checkout this folder for faster clones)

### Step 3: Save and Build

Click **Save** → **Build Now**

Jenkins will:
1. Clone the repository
2. Look for `jenkins/Jenkinsfile-PC-Tests`
3. Execute the pipeline

---

## 📋 Detailed Configuration

### Full Pipeline Configuration

```
Pipeline Definition: Pipeline script from SCM

SCM: Git
  Repository URL: https://bitbucket.org/your-company/performance-tests.git
  
  Credentials: bitbucket-credentials (click Add to create)
  
  Branches to build: */main
  
  Repository browser: (Auto)
  
  Script Path: jenkins/Jenkinsfile-PC-Tests  ← CRITICAL!
  
  Lightweight checkout: ☐ (unchecked for now)
```

---

## 🔐 Setting Up Credentials

### Option A: HTTPS Credentials

1. **Jenkins → Credentials → System → Global credentials → Add Credentials**
2. **Configuration:**
   ```
   Kind: Username with password
   Scope: Global
   Username: your-bitbucket-username
   Password: your-bitbucket-app-password  ← NOT your account password!
   ID: bitbucket-credentials
   Description: Bitbucket Access
   ```

3. **Create Bitbucket App Password:**
   - Go to Bitbucket → Personal Settings → App passwords
   - Click "Create app password"
   - Label: Jenkins Access
   - Permissions: ✓ Repositories - Read
   - Copy the generated password
   - Use in Jenkins credentials

### Option B: SSH Key (Recommended)

1. **Generate SSH Key on Jenkins Server:**
   ```bash
   ssh-keygen -t rsa -b 4096 -C "jenkins@company.com"
   # Save to: /home/jenkins/.ssh/bitbucket_rsa
   # No passphrase (or use passphrase for extra security)
   
   cat /home/jenkins/.ssh/bitbucket_rsa.pub
   # Copy this public key
   ```

2. **Add Public Key to Bitbucket:**
   - Bitbucket → Personal Settings → SSH keys
   - Click "Add key"
   - Paste public key
   - Label: Jenkins Server

3. **Add Private Key to Jenkins:**
   - Jenkins → Credentials → Add Credentials
   ```
   Kind: SSH Username with private key
   Scope: Global
   ID: bitbucket-ssh-key
   Username: git
   Private Key: Enter directly
   [Paste private key content]
   Passphrase: (if you set one)
   ```

4. **Use SSH URL in Jenkins:**
   ```
   git@bitbucket.org:your-company/your-repo.git
   ```

---

## 📁 Recommended Repository Structure

### Option 1: Jenkins Folder (Recommended)

```
your-repo/
├── jenkins/
│   ├── Jenkinsfile-PC-Scheduled        ← Main scheduled pipeline
│   ├── Jenkinsfile-PC-OnDemand         ← Manual execution pipeline
│   ├── Jenkinsfile-PC-Staging          ← Staging environment
│   ├── scripts/
│   │   ├── parse_pc_report.py          ← Parser script
│   │   ├── load_to_oracle.py           ← Oracle loader
│   │   └── utils.py                    ← Shared utilities
│   ├── config/
│   │   ├── pc-config-prod.properties   ← Production config
│   │   ├── pc-config-staging.properties
│   │   └── oracle-config.properties
│   └── sql/
│       ├── create_tables.sql
│       └── queries.sql
├── src/                                 ← Your application code
├── tests/                               ← Other tests
└── README.md
```

**Jenkins Job Configuration:**
- Script Path: `jenkins/Jenkinsfile-PC-Scheduled`

### Option 2: Root Level (Simple)

```
your-repo/
├── Jenkinsfile                          ← At root
├── scripts/
│   ├── parse_pc_report.py
│   └── load_to_oracle.py
├── src/
└── README.md
```

**Jenkins Job Configuration:**
- Script Path: `Jenkinsfile` (default)

### Option 3: CI/CD Folder

```
your-repo/
├── .ci/
│   ├── Jenkinsfile
│   ├── parse_report.py
│   └── load_oracle.py
├── src/
└── README.md
```

**Jenkins Job Configuration:**
- Script Path: `.ci/Jenkinsfile`

---

## 🔧 Jenkinsfile Adjustments for SCM

When using SCM, adjust your Jenkinsfile:

### 1. Use Relative Paths

```groovy
stage('Setup Scripts') {
    steps {
        script {
            // Scripts are already in workspace from SCM checkout
            sh """
                chmod +x ${WORKSPACE}/jenkins/scripts/parse_pc_report.py
                chmod +x ${WORKSPACE}/jenkins/scripts/load_to_oracle.py
            """
        }
    }
}

stage('Parse Report') {
    steps {
        script {
            sh """
                python3 ${WORKSPACE}/jenkins/scripts/parse_pc_report.py \
                    ${WORKSPACE}/results/index.html \
                    ${WORKSPACE}/results/transactions_data.json
            """
        }
    }
}
```

### 2. Don't Create Scripts Inline

**❌ Bad (for SCM):**
```groovy
sh """
cat > ${WORKSPACE}/scripts/parse_report.py << 'PYEOF'
#!/usr/bin/env python3
...
PYEOF
"""
```

**✅ Good (for SCM):**
```groovy
// Scripts already available from SCM checkout
sh "python3 ${WORKSPACE}/jenkins/scripts/parse_pc_report.py ..."
```

### 3. Load Config from Repository

```groovy
stage('Load Configuration') {
    steps {
        script {
            def props = readProperties file: 'jenkins/config/pc-config-prod.properties'
            env.PC_HOST = props.PC_HOST
            env.ORACLE_DSN = props.ORACLE_DSN
        }
    }
}
```

---

## 🎯 Complete Example

### Repository Structure:
```
performance-automation/
├── jenkins/
│   ├── Jenkinsfile
│   ├── scripts/
│   │   ├── parse_pc_report.py
│   │   └── load_to_oracle.py
│   └── config/
│       └── production.properties
└── README.md
```

### Jenkins Job Configuration:
```
Name: PC-Daily-Scheduled-Tests
Type: Pipeline

Pipeline:
  Definition: Pipeline script from SCM
  SCM: Git
    Repository URL: git@bitbucket.org:mycompany/performance-automation.git
    Credentials: bitbucket-ssh-key
    Branch: */main
    Script Path: jenkins/Jenkinsfile
```

### Jenkinsfile (jenkins/Jenkinsfile):
```groovy
pipeline {
    agent any
    
    triggers {
        cron('0 2 * * *')
    }
    
    stages {
        stage('Preparation') {
            steps {
                script {
                    echo "Repository checked out to: ${WORKSPACE}"
                    echo "Scripts location: ${WORKSPACE}/jenkins/scripts"
                    
                    // Make scripts executable
                    sh """
                        chmod +x ${WORKSPACE}/jenkins/scripts/*.py
                    """
                }
            }
        }
        
        stage('Run PC Test') {
            steps {
                script {
                    // Your PC test execution code
                    echo "Executing PC test..."
                }
            }
        }
        
        stage('Parse Report') {
            steps {
                script {
                    sh """
                        python3 ${WORKSPACE}/jenkins/scripts/parse_pc_report.py \
                            ${WORKSPACE}/results/index.html \
                            --output-json ${WORKSPACE}/results/data.json \
                            --print-summary
                    """
                }
            }
        }
        
        stage('Load to Oracle') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: 'oracle-credentials',
                        usernameVariable: 'ORACLE_USER',
                        passwordVariable: 'ORACLE_PASS'
                    )]) {
                        sh """
                            python3 ${WORKSPACE}/jenkins/scripts/load_to_oracle.py \
                                --json-file ${WORKSPACE}/results/data.json \
                                --oracle-user ${ORACLE_USER} \
                                --oracle-password ${ORACLE_PASS} \
                                --oracle-dsn ${params.ORACLE_DSN} \
                                --run-id ${RUN_ID}
                        """
                    }
                }
            }
        }
    }
}
```

---

## 🔄 Branch Strategies

### Single Branch (Simple)
```
Branches to build: */main
Script Path: jenkins/Jenkinsfile
```

### Multi-Branch Pipeline (Advanced)

For different environments:

```
main branch    → jenkins/Jenkinsfile-Production
develop branch → jenkins/Jenkinsfile-Staging
feature/*      → jenkins/Jenkinsfile-Dev
```

Configure Multi-branch Pipeline:
1. New Item → Multibranch Pipeline
2. Branch Sources → Bitbucket
3. Script Path: jenkins/Jenkinsfile
4. Jenkins will discover all branches automatically

---

## ✅ Verification Steps

### After Configuration:

1. **Check SCM Polling:**
   ```
   Jenkins Job → Configure → Build Triggers
   ☑ Poll SCM
   Schedule: H/5 * * * *  (every 5 minutes)
   ```

2. **Verify Checkout:**
   ```
   Build Now → Console Output
   
   Should see:
   > git init
   > git fetch
   > git checkout -f [commit-hash]
   Checking out Revision [hash]
   ```

3. **Verify Script Path:**
   ```
   Console should show:
   Loading Jenkinsfile from jenkins/Jenkinsfile-PC-Tests
   ```

4. **Test Script Access:**
   ```
   Add a test stage:
   
   stage('Verify Scripts') {
       steps {
           sh "ls -la ${WORKSPACE}/jenkins/scripts/"
           sh "python3 ${WORKSPACE}/jenkins/scripts/parse_pc_report.py --help"
       }
   }
   ```

---

## 🚨 Common Issues & Solutions

### Issue 1: "Jenkinsfile not found"

**Error:** `Couldn't find any revision to build`

**Solution:** Check Script Path
```
Correct: jenkins/Jenkinsfile-PC-Tests
Wrong:   /jenkins/Jenkinsfile-PC-Tests  (no leading slash!)
Wrong:   jenkins\Jenkinsfile-PC-Tests   (use forward slash)
```

### Issue 2: "Permission denied" on scripts

**Error:** `Permission denied: ./parse_pc_report.py`

**Solution:** Make scripts executable in Jenkinsfile
```groovy
sh "chmod +x ${WORKSPACE}/jenkins/scripts/*.py"
```

### Issue 3: Credentials not working

**Error:** `Authentication failed`

**Solution:** 
- For HTTPS: Use Bitbucket App Password, not account password
- For SSH: Verify public key is added to Bitbucket
- Test credentials: `git ls-remote [repo-url]`

### Issue 4: Can't find scripts in pipeline

**Error:** `No such file or directory: scripts/parse_report.py`

**Solution:** Use absolute paths
```groovy
# Wrong
sh "python3 scripts/parse_report.py"

# Correct
sh "python3 ${WORKSPACE}/jenkins/scripts/parse_report.py"
```

---

## 📝 Best Practices

### 1. Use Relative Paths from WORKSPACE
```groovy
def scriptsDir = "${WORKSPACE}/jenkins/scripts"
def configDir = "${WORKSPACE}/jenkins/config"

sh "python3 ${scriptsDir}/parse_report.py"
```

### 2. Version Control Everything
```
✓ Jenkinsfile
✓ Python scripts
✓ Configuration files
✓ SQL scripts
✗ Credentials (use Jenkins credentials store)
✗ Passwords (use environment variables)
```

### 3. Use .gitignore
```
# .gitignore
results/
*.pyc
__pycache__/
*.log
.env
credentials.properties
```

### 4. Document in README
```markdown
# Jenkins Setup

## Pipeline Configuration
- Script Path: `jenkins/Jenkinsfile-PC-Scheduled`
- Branch: main
- Schedule: Daily at 2 AM

## Required Credentials
- `bitbucket-credentials`: Bitbucket access
- `pc-credentials`: Performance Center
- `oracle-credentials`: Oracle database
```

---

## 🎯 Summary

**To use Jenkinsfile from Bitbucket folder:**

1. **Script Path Setting:** `jenkins/Jenkinsfile-PC-Tests` ✓
2. **Add Credentials:** Bitbucket access (HTTPS or SSH) ✓
3. **Use Relative Paths:** `${WORKSPACE}/jenkins/scripts/` ✓
4. **Don't Create Scripts Inline:** Scripts from SCM ✓
5. **Test Before Production:** Verify checkout and paths ✓

**Your Jenkinsfile will be loaded from the folder you specify!** 🚀