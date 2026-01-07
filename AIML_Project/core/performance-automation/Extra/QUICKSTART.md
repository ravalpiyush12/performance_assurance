# Quick Start Guide - 5 Minutes Setup

## Prerequisites Checklist
- [ ] Jenkins server with Pipeline plugin
- [ ] Python 3.7+ installed on Jenkins agent
- [ ] Performance Center server accessible
- [ ] PC user credentials

## Step-by-Step Setup

### 1️⃣ Add Performance Center Credentials to Jenkins (2 min)

1. Open Jenkins → **Manage Jenkins** → **Manage Credentials**
2. Click **Global** → **Add Credentials**
3. Fill in:
   ```
   Kind: Username with password
   Username: [Your PC Username]
   Password: [Your PC Password]
   ID: pc-credentials
   Description: Performance Center Credentials
   ```
4. Click **OK**

### 2️⃣ Create Jenkins Pipeline Job (1 min)

1. Jenkins Dashboard → **New Item**
2. Enter name: `PC-Load-Test-Automation`
3. Select **Pipeline**
4. Click **OK**

### 3️⃣ Configure Pipeline Script (2 min)

1. Scroll to **Pipeline** section
2. Select **Definition**: `Pipeline script`
3. Copy the **entire Jenkinsfile** content and paste into the script box
4. **IMPORTANT**: Update these default values in the script:
   ```groovy
   // Find these lines and update:
   defaultValue: 'your-pc-server.company.com'  // Line ~8
   defaultValue: 'YOUR_DOMAIN'                  // Line ~13
   defaultValue: 'YOUR_PROJECT'                 // Line ~18
   defaultValue: 'team@company.com'            // Line ~43
   ```
5. Click **Save**

### 4️⃣ First Test Run

1. Click **Build with Parameters**
2. Verify/Update parameters:
   ```
   PC_SERVER: pc.mycompany.com
   PC_DOMAIN: DEFAULT
   PC_PROJECT: MyProject
   TEST_ID: 1
   TEST_DURATION: 600 (10 minutes for testing)
   EMAIL_RECIPIENTS: your-email@company.com
   ```
3. Click **Build**
4. Watch the console output

### 5️⃣ View Results

After the build completes:
- Click **Performance Test Report** for HTML report
- Click **Artifacts** to download Excel/JSON files
- Check your email for the summary

---

## 🎯 What Happens When You Run

```
1. Preparation         [30s]  → Setup environment
2. Trigger Test        [30s]  → Start PC test
3. Monitor             [Varies] → Wait for completion
4. Download Results    [2m]   → Get analysis data
5. Analyze             [1m]   → Process statistics
6. Generate Reports    [1m]   → Create HTML/Excel
7. Send Email          [10s]  → Notify team
```

---

## 🔧 Common First-Time Issues

### Issue: "Authentication Failed"
**Fix**: 
- Double-check credentials in Jenkins
- Verify PC username/password are correct
- Test PC login manually first

### Issue: "Test Not Found"
**Fix**:
- Verify TEST_ID exists in your PC project
- Check PC_DOMAIN and PC_PROJECT names are correct
- Ensure test is not archived

### Issue: "Python module not found"
**Fix**:
```bash
# SSH to Jenkins agent and run:
pip3 install --user requests pandas openpyxl
```

---

## 📝 Quick Reference

### PC Server URL Format
```
Correct: pc-server.company.com
Wrong:   http://pc-server.company.com
Wrong:   pc-server.company.com:8080
```

### Test Duration Examples
```
600   = 10 minutes (good for testing)
1800  = 30 minutes
3600  = 1 hour
7200  = 2 hours
```

### Post Run Actions
- `COLLATE_AND_ANALYZE` → Full analysis (recommended)
- `COLLATE` → Collect results only
- `DO_NOTHING` → Just run the test

---

## 🆘 Need Help?

If something doesn't work:

1. **Check Jenkins Console Output**
   - Build → Console Output
   - Look for error messages

2. **Check PC Server**
   - Can you login to PC web UI?
   - Is the test runnable manually?

3. **Check Python**
   ```bash
   # On Jenkins agent:
   python3 --version
   pip3 list | grep -E "requests|pandas"
   ```

4. **Test PC Connection**
   ```bash
   # From Jenkins agent:
   curl -v http://your-pc-server:8080/LoadTest/rest/
   ```

---

## 🎉 Success Indicators

You'll know it's working when you see:

```
✓ Authentication successful!
✓ Test triggered successfully!
  Run ID: 12345
✓ Test completed with status: FINISHED
✓ Results downloaded successfully!
✓ Analysis completed successfully!
✓ Email notification sent!
```

---

## 📚 Next Steps

Once your first test runs successfully:

1. **Customize Reports**
   - Edit `results_analyzer.py`
   - Add your transaction names
   - Define your SLA thresholds

2. **Schedule Regular Tests**
   - Add Build Triggers in Jenkins
   - Example: `H 2 * * 1-5` (weekdays at 2 AM)

3. **Integrate with CI/CD**
   - Trigger from deployment pipeline
   - Add performance gates

4. **Setup Trending**
   - Store results in database
   - Create Grafana dashboards
   - Track performance over time

---

**Ready? Let's go! 🚀**

For detailed documentation, see `README.md`
