# Testing Guide & Examples

## Test Scenarios

### Scenario 1: Quick Smoke Test (10 minutes)
**Purpose**: Verify the automation works end-to-end

```
Parameters:
- TEST_ID: Your test ID
- TEST_DURATION: 600 (10 minutes)
- POST_RUN_ACTION: COLLATE_AND_ANALYZE
- POLL_INTERVAL: 30 (check every 30 seconds)
```

**Expected Result**: Complete in ~15 minutes total
- Trigger: 30s
- Execution: 10 min
- Download/Analysis: 3 min

---

### Scenario 2: Standard Load Test (30 minutes)
**Purpose**: Regular performance testing

```
Parameters:
- TEST_ID: Your test ID
- TEST_DURATION: 1800 (30 minutes)
- POST_RUN_ACTION: COLLATE_AND_ANALYZE
- POLL_INTERVAL: 60
```

**Expected Result**: Complete in ~40 minutes total

---

### Scenario 3: Extended Soak Test (2 hours)
**Purpose**: Long-running stability test

```
Parameters:
- TEST_ID: Your test ID
- TEST_DURATION: 7200 (2 hours)
- POST_RUN_ACTION: COLLATE_AND_ANALYZE
- POLL_INTERVAL: 120 (check every 2 minutes)
```

**Expected Result**: Complete in ~2.5 hours total

---

## Manual Testing Before Automation

### Step 1: Verify PC Connectivity
```bash
# Test from command line
curl -X POST http://your-pc-server/LoadTest/rest/authentication-point/authenticate \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'

# Expected: 200 OK with authentication token
```

### Step 2: Verify Test Availability
1. Login to Performance Center web UI
2. Navigate to your project
3. Find your test by ID
4. Verify test status is "Ready"
5. Note down the exact Test ID

### Step 3: Test Manual Trigger
1. In PC web UI, manually run the test
2. Wait for it to start
3. Stop the test (don't wait for completion)
4. This confirms the test works

---

## Validating Automation Output

### What to Check After Each Run

#### 1. Jenkins Console Output
Look for these success indicators:
```
✓ Authentication successful!
✓ Test triggered successfully!
✓ Test completed with status: FINISHED
✓ Results downloaded successfully!
✓ Analysis completed successfully!
```

#### 2. Generated Files
Check these files exist in workspace:
```
results/
  ├── run_info.json          # Trigger confirmation
  ├── execution_log.json     # Monitoring log
  ├── metadata_12345.json    # Test metadata
  ├── report_12345.html      # PC report
  ├── results_12345.zip      # Raw results
  ├── analysis_summary.json  # Analysis output
  ├── performance_data.xlsx  # Excel report
  └── final_report.html      # Pretty HTML report
```

#### 3. HTML Report Content
The final report should show:
- Test summary with run ID
- SLA status (PASSED/FAILED)
- Executive summary cards
- SLA results table
- Transaction details table

#### 4. Email Notification
Email should contain:
- Subject line with build number and status
- Summary table with key metrics
- Links to Jenkins report and build
- Excel attachment (if configured)

---

## Common Test Results

### Expected Good Results
```json
{
  "run_id": "12345",
  "status": "FINISHED",
  "total_transactions": 13500,
  "passed_transactions": 13380,
  "failed_transactions": 120,
  "success_rate": 99.11,
  "failure_rate": 0.89,
  "avg_response_time": 1.20,
  "sla_passed": true
}
```

### Expected Results with SLA Failure
```json
{
  "run_id": "12346",
  "status": "FINISHED",
  "total_transactions": 10000,
  "passed_transactions": 9500,
  "failed_transactions": 500,
  "success_rate": 95.00,
  "failure_rate": 5.00,
  "avg_response_time": 3.50,
  "sla_passed": false
}
```

---

## Debugging Failed Runs

### Debug Checklist

1. **Check Jenkins Console for Exact Error**
   ```
   Build → Console Output → Search for "✗" or "Error"
   ```

2. **Verify Credentials**
   ```bash
   # Test authentication manually
   python3 scripts/pc_automation.py trigger \
     --server "pc-server" \
     --domain "DEFAULT" \
     --project "MyProject" \
     --username "user" \
     --password "pass" \
     --test-id "1" \
     --duration "600" \
     --output "/tmp/test.json"
   ```

3. **Check Test Status in PC**
   - Login to PC web UI
   - Check if test is stuck
   - Check if there are resource issues

4. **Check Python Dependencies**
   ```bash
   pip3 list | grep -E "requests|pandas|openpyxl"
   ```

5. **Check Disk Space**
   ```bash
   df -h
   # Ensure workspace has enough space
   ```

---

## Performance Benchmarks

### Pipeline Stage Durations (Approximate)

| Stage | Duration | Notes |
|-------|----------|-------|
| Preparation | 30-60s | Environment setup |
| Setup Python | 10-30s | Install dependencies |
| Checkout Scripts | 5-10s | Script preparation |
| Trigger Test | 20-40s | API call to PC |
| Monitor (10 min test) | 10-12 min | Includes poll overhead |
| Monitor (30 min test) | 30-35 min | Includes poll overhead |
| Download Results | 1-5 min | Depends on result size |
| Analyze Results | 30-90s | Processing time |
| Generate Reports | 30-60s | HTML/Excel creation |
| Publish Results | 10-20s | Jenkins publishing |
| Send Email | 5-15s | SMTP delivery |

### Total Time Examples

**10-minute test**: ~15 minutes total
**30-minute test**: ~40 minutes total  
**1-hour test**: ~70 minutes total
**2-hour test**: ~135 minutes total

---

## Maintenance & Cleanup

### Regular Cleanup Tasks

1. **Archive Old Results** (Weekly)
   ```bash
   # Keep last 30 days only
   find $WORKSPACE/results -mtime +30 -delete
   ```

2. **Check Disk Usage** (Daily)
   ```bash
   du -sh $WORKSPACE/results
   ```

3. **Review Failed Builds** (Daily)
   - Investigate any failed builds
   - Update SLA thresholds if needed
   - Fix any infrastructure issues

4. **Update Dependencies** (Monthly)
   ```bash
   pip3 install --upgrade requests pandas openpyxl
   ```

---

## Sample Test Plan

### Week 1: Setup & Validation
- Day 1: Setup automation, run 10-min smoke test
- Day 2: Run 30-min load test
- Day 3: Validate reports and email
- Day 4: Fine-tune SLA thresholds
- Day 5: Document baseline metrics

### Week 2: Integration
- Integrate with CI/CD pipeline
- Setup scheduled runs
- Create dashboards
- Train team members

### Week 3: Optimization
- Optimize report generation
- Add custom metrics
- Setup trending
- Create runbooks

---

## Success Criteria

Your automation is successful when:

✅ Tests trigger reliably (>95% success rate)
✅ Monitoring completes without timeouts
✅ Reports are generated consistently
✅ Emails are delivered on time
✅ Team uses reports for decisions
✅ SLA thresholds are meaningful
✅ No manual intervention needed

---

## Tips for Better Testing

1. **Start with short tests** - Validate automation before long tests
2. **Use consistent test data** - Helps with trend analysis
3. **Document baselines** - Know what "good" looks like
4. **Review trends weekly** - Catch degradation early
5. **Update SLAs regularly** - As system improves
6. **Share reports widely** - Increase visibility
7. **Automate everything** - No manual steps
8. **Monitor Jenkins health** - Keep agents healthy

---

**Happy Testing! 🎯**
