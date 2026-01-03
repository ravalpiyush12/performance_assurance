# Troubleshooting Guide: "CreateProcess error=2"

## Understanding the Error

**Error Message:**
```
Java IO Error: CreateProcess error=2, The system cannot find the file specified
```

**What it means:**
- Jenkins is trying to run a command/script that doesn't exist
- The file path is incorrect
- The required tool (python, curl, etc.) is not in PATH

---

## Solution 1: Use Standalone Jenkinsfile (RECOMMENDED)

I've created **Jenkinsfile-Standalone** that doesn't need any external Python scripts.

### Steps:

1. **Copy the NEW standalone Jenkinsfile**
   - Use: `Jenkinsfile-Standalone` 
   - This version has everything embedded

2. **Adjust for Your OS:**

   **If Jenkins is on Windows:**
   - Keep `bat` commands as-is
   - Ensure curl is installed

   **If Jenkins is on Linux:**
   - Replace all `bat` with `sh`
   - Replace `^` with `\` for line continuation
   - Update path separators from `\` to `/`

3. **Install curl on Windows (if needed):**
   ```cmd
   # Download curl for Windows
   # Or use PowerShell instead
   ```

---

## Solution 2: Test Your Setup First

Use the **Jenkinsfile-Test** to verify your Jenkins setup works.

### Steps:

1. Create a NEW pipeline job: `Test-Jenkins-Setup`
2. Copy **Jenkinsfile-Test** content
3. Click **Build**
4. If this works, your Jenkins is configured correctly

### Expected Output:
```
✓ curl is available
✓ Directory created successfully  
✓ Report generated
✓ Report published
✓ ALL CHECKS PASSED!
```

---

## Solution 3: Fix the Original Jenkinsfile

The original Jenkinsfile tries to call Python scripts. Here's how to fix it:

### Option A: Remove Python Script References

Change this:
```groovy
sh """
    python3 pc_automation.py trigger ...
"""
```

To this:
```groovy
// Use direct curl commands instead
sh """
    curl -X POST ...
"""
```

### Option B: Create Scripts in Workspace

Add a stage to create scripts first:

```groovy
stage('Setup Scripts') {
    steps {
        script {
            // Create pc_automation.py in workspace
            writeFile file: 'pc_automation.py', text: '''
#!/usr/bin/env python3
# Your Python code here
'''
            
            // For Linux
            sh 'chmod +x pc_automation.py'
            
            // For Windows - no chmod needed
        }
    }
}
```

---

## Quick Fixes by Operating System

### Windows Jenkins

**Replace this pattern:**
```groovy
sh "python3 script.py"  // ✗ WRONG on Windows
```

**With this:**
```groovy
bat "python script.py"  // ✓ CORRECT on Windows
```

**Full example:**
```groovy
stage('Test') {
    steps {
        script {
            bat 'echo Hello'
            bat 'dir'
            bat 'curl --version'
        }
    }
}
```

### Linux Jenkins

**Keep this pattern:**
```groovy
sh "python3 script.py"  // ✓ CORRECT on Linux
sh "curl --version"
```

---

## Common Issues & Fixes

### Issue 1: Python not found

**Error:**
```
'python3' is not recognized as an internal or external command
```

**Fix:**
```groovy
// Check if Python exists first
stage('Check Python') {
    steps {
        script {
            // For Windows
            bat 'python --version || echo Python not found'
            
            // For Linux
            sh 'python3 --version || echo Python not found'
        }
    }
}
```

### Issue 2: curl not found

**Error:**
```
'curl' is not recognized as an internal or external command
```

**Fix for Windows:**
1. Download curl: https://curl.se/windows/
2. Add to PATH
3. Restart Jenkins

**Alternative - Use PowerShell:**
```groovy
powershell """
    Invoke-WebRequest -Uri "http://..." -Method POST
"""
```

### Issue 3: File path issues

**Error:**
```
The system cannot find the path specified
```

**Fix:**
```groovy
// Always use ${WORKSPACE}
bat "mkdir ${WORKSPACE}\\results"  // Windows
sh "mkdir -p ${WORKSPACE}/results"  // Linux
```

### Issue 4: Line continuation errors

**Windows - Use ^:**
```groovy
bat """
    curl -X POST "http://server" ^
    -H "Content-Type: json" ^
    -d "data"
"""
```

**Linux - Use \:**
```groovy
sh """
    curl -X POST "http://server" \\
    -H "Content-Type: json" \\
    -d "data"
"""
```

---

## Step-by-Step Recovery

### Step 1: Identify Your OS
```groovy
stage('Identify OS') {
    steps {
        script {
            if (isUnix()) {
                echo "Running on Linux/Unix"
                sh 'uname -a'
            } else {
                echo "Running on Windows"
                bat 'ver'
            }
        }
    }
}
```

### Step 2: Use Correct Jenkinsfile

**For Windows:** Use `Jenkinsfile-Standalone` with `bat` commands

**For Linux:** Use `Jenkinsfile-Standalone` and change:
- All `bat` → `sh`
- All `^` → `\`
- All `\\` → `/`

### Step 3: Test Basic Functionality

Run `Jenkinsfile-Test` first to verify:
- ✓ Jenkins can execute commands
- ✓ Workspace is accessible
- ✓ Required tools are available

### Step 4: Add PC Integration

Once basic test works, add PC API calls:
```groovy
stage('Test PC Connection') {
    steps {
        script {
            // For Windows
            bat 'curl -X GET http://${params.PC_SERVER}/LoadTest/rest/'
            
            // For Linux
            sh 'curl -X GET http://${params.PC_SERVER}/LoadTest/rest/'
        }
    }
}
```

---

## Verification Checklist

Before running the full pipeline, verify:

- [ ] Jenkins agent has curl installed
- [ ] Jenkins agent can reach PC server
- [ ] Credentials are configured (ID: pc-credentials)
- [ ] Workspace has write permissions
- [ ] Correct shell command (bat vs sh)
- [ ] HTML Publisher plugin is installed
- [ ] Email Extension plugin is installed (for notifications)

---

## Which Jenkinsfile to Use?

### Use Jenkinsfile-Test if:
- First time setting up
- Getting errors
- Want to verify Jenkins works

### Use Jenkinsfile-Standalone if:
- Test passed
- Need full automation
- Don't want external scripts

### Use Original Jenkinsfile if:
- Have Python installed
- Want modular scripts
- Need advanced customization

---

## Testing Your Fix

### Test 1: Basic Pipeline
```groovy
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                script {
                    echo "If you see this, Jenkins works!"
                    bat 'echo Windows' // or sh 'echo Linux'
                }
            }
        }
    }
}
```

If this works → Jenkins is OK

### Test 2: File Operations
```groovy
stage('Test Files') {
    steps {
        script {
            bat 'mkdir test_dir'  // or sh 'mkdir -p test_dir'
            bat 'echo test > test_dir\\test.txt'
        }
    }
}
```

If this works → File system is OK

### Test 3: Network
```groovy
stage('Test Network') {
    steps {
        script {
            bat 'curl https://google.com'  // or sh
        }
    }
}
```

If this works → Network + curl is OK

---

## Get Help

If still stuck, provide these details:

1. **Your Jenkins OS:**
   ```
   Windows/Linux?
   Version?
   ```

2. **Error Message:**
   ```
   Copy exact error from console
   ```

3. **Which Jenkinsfile:**
   ```
   Original? Standalone? Test?
   ```

4. **Console Output:**
   ```
   Full console log
   ```

---

## Next Steps

1. ✅ First: Try **Jenkinsfile-Test**
2. ✅ Second: Use **Jenkinsfile-Standalone** 
3. ✅ Third: Adjust for your OS (bat vs sh)
4. ✅ Fourth: Run and check console output

**The standalone version should work without any external dependencies!**
