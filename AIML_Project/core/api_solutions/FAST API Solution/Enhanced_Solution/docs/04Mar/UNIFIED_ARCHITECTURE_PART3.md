# 🎨 UI Components - Part 3: AWR Tab & Performance Center Tab

## 📝 INCREMENTAL CHANGE #1: Add AWR Tab Content

**File:** `index.html`  
**Location:** Find the existing AWR tab placeholder `<div id="awr" class="tab-content">`

**REPLACE THIS:**
```html
<div id="awr" class="tab-content">
    <h2>AWR Analysis</h2>
    <p>Automatic Workload Repository Analysis</p>
</div>
```

**WITH THIS COMPLETE AWR TAB:**
```html
<!-- AWR Analysis Tab -->
<div id="awr" class="tab-content">
    <h2>📊 AWR Analysis</h2>
    <p style="color: #666; margin-bottom: 20px;">
        Upload Oracle AWR HTML reports for automated performance analysis for <span id="awrLobName" style="font-weight: bold; color: #667eea;"></span>
    </p>
    
    <!-- Upload Section -->
    <div class="appd-section">
        <h3>📤 Upload AWR Report</h3>
        <p style="color: #666; margin-bottom: 15px;">
            Upload AWR HTML report to analyze database performance and identify concerns
        </p>
        
        <div class="form-group">
            <label>Performance Center Run ID: *</label>
            <input type="text" id="awrPcRunId" placeholder="e.g., 35678" required>
            <small style="color: #666;">LoadRunner/PC run ID that this analysis is linked to</small>
        </div>
        
        <div class="form-group">
            <label>Database Name: *</label>
            <input type="text" id="awrDatabaseName" placeholder="e.g., PRODDB" required>
        </div>
        
        <div class="form-group">
            <label>Test Name (Optional):</label>
            <input type="text" id="awrTestName" placeholder="e.g., Peak Load Test">
        </div>
        
        <div class="form-group">
            <label>AWR Report (HTML): *</label>
            <input type="file" id="awrFileInput" accept=".html,.htm" required 
                   style="padding: 10px; border: 2px dashed #667eea; border-radius: 6px; background: #f9f9f9;">
            <small style="color: #666; display: block; margin-top: 5px;">
                Select the AWR HTML report file from Oracle
            </small>
        </div>
        
        <button class="btn btn-success" onclick="uploadAWRReport()">
            📤 Upload & Analyze Report
        </button>
        
        <div id="awrUploadStatus" style="display: none; margin-top: 15px;"></div>
    </div>
    
    <!-- Analysis Results Section -->
    <div class="appd-section" id="awrResultsSection" style="display: none;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="margin: 0;">📋 Analysis Results</h3>
            <span id="awrResultsBadge" class="session-status running" style="font-size: 0.9em;"></span>
        </div>
        
        <!-- Summary Cards -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #667eea;">
                <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">Database</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #333;" id="awrDbName">--</div>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #667eea;">
                <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">Snapshot Range</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #333;" id="awrSnapRange">--</div>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #667eea;">
                <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">Elapsed Time</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #333;" id="awrElapsed">--</div>
            </div>
        </div>
        
        <!-- Concerns Summary -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px;">
            <div class="concern-card critical-card">
                <div class="concern-count" id="awrCriticalCount">0</div>
                <div class="concern-label">Critical</div>
            </div>
            <div class="concern-card warning-card">
                <div class="concern-count" id="awrWarningCount">0</div>
                <div class="concern-label">Warning</div>
            </div>
            <div class="concern-card info-card">
                <div class="concern-count" id="awrInfoCount">0</div>
                <div class="concern-label">Info</div>
            </div>
        </div>
        
        <!-- Concerns Details -->
        <div id="awrConcernsContainer"></div>
    </div>
    
    <!-- Recent Analyses -->
    <div class="appd-section">
        <h3>📚 Recent AWR Analyses</h3>
        <div id="awrRecentList">
            <p style="text-align: center; color: #999;">No recent analyses</p>
        </div>
    </div>
</div>

<style>
/* AWR Concern Cards */
.concern-card {
    padding: 20px;
    border-radius: 6px;
    text-align: center;
}

.critical-card {
    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
    color: white;
}

.warning-card {
    background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
    color: white;
}

.info-card {
    background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
    color: white;
}

.concern-count {
    font-size: 2.5em;
    font-weight: bold;
    margin-bottom: 5px;
}

.concern-label {
    font-size: 0.9em;
    opacity: 0.9;
}

.concern-item {
    background: white;
    padding: 20px;
    margin-bottom: 15px;
    border-radius: 6px;
    border-left: 4px solid #ccc;
}

.concern-item.critical {
    border-left-color: #dc3545;
    background: #fef1f0;
}

.concern-item.warning {
    border-left-color: #ffc107;
    background: #fff9e6;
}

.concern-item.info {
    border-left-color: #17a2b8;
    background: #e3f2fd;
}

.concern-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.concern-title {
    font-weight: bold;
    font-size: 1.1em;
    color: #333;
}

.concern-severity-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.8em;
    font-weight: 600;
}

.concern-severity-badge.critical {
    background: #dc3545;
    color: white;
}

.concern-severity-badge.warning {
    background: #ffc107;
    color: #333;
}

.concern-severity-badge.info {
    background: #17a2b8;
    color: white;
}

.concern-description {
    color: #666;
    margin-bottom: 10px;
    line-height: 1.5;
}

.concern-recommendation {
    background: white;
    padding: 12px;
    border-radius: 4px;
    border-left: 3px solid #28a745;
    margin-top: 10px;
}

.concern-recommendation strong {
    color: #28a745;
}

.concern-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 10px;
    margin-top: 10px;
}

.concern-metric {
    background: white;
    padding: 10px;
    border-radius: 4px;
    text-align: center;
}

.metric-value {
    font-size: 1.3em;
    font-weight: bold;
    color: #667eea;
}

.metric-label {
    font-size: 0.8em;
    color: #666;
    margin-top: 3px;
}
</style>
```

---

## 📝 INCREMENTAL CHANGE #2: Add Performance Center Tab Content

**File:** `index.html`  
**Location:** Find the existing LoadRunner/PC tab `<div id="loadrunner" class="tab-content">`

**REPLACE THIS:**
```html
<div id="loadrunner" class="tab-content">
    <h2>LoadRunner Test Results</h2>
    <p>Fetch and analyze LoadRunner performance test results</p>
</div>
```

**WITH THIS COMPLETE PC TAB:**
```html
<!-- Performance Center Tab -->
<div id="loadrunner" class="tab-content">
    <h2>🧪 Performance Center - LoadRunner Results</h2>
    <p style="color: #666; margin-bottom: 20px;">
        Fetch LoadRunner test results from Performance Center for <span id="lrLobName" style="font-weight: bold; color: #667eea;"></span>
    </p>
    
    <!-- Connection Section -->
    <div class="appd-section">
        <h3>🔗 Connect to Performance Center</h3>
        <p style="color: #666; margin-bottom: 15px;">
            Provide Performance Center connection details to fetch test results
        </p>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div class="form-group">
                <label>PC URL: *</label>
                <input type="text" id="pcUrl" placeholder="http://pc-server.domain.com" required>
            </div>
            
            <div class="form-group">
                <label>Port:</label>
                <input type="number" id="pcPort" value="8080" placeholder="8080">
            </div>
            
            <div class="form-group">
                <label>Domain: *</label>
                <input type="text" id="pcDomain" placeholder="DEFAULT" required>
            </div>
            
            <div class="form-group">
                <label>Project: *</label>
                <input type="text" id="pcProject" placeholder="MyProject" required>
            </div>
            
            <div class="form-group">
                <label>Username: *</label>
                <input type="text" id="pcUsername" placeholder="username" required>
            </div>
            
            <div class="form-group">
                <label>Password: *</label>
                <input type="password" id="pcPassword" placeholder="password" required>
            </div>
        </div>
        
        <div class="form-group">
            <label>PC Run ID: *</label>
            <input type="text" id="pcRunId" placeholder="e.g., 35678" required>
            <small style="color: #666;">The Performance Center test run ID</small>
        </div>
        
        <div class="form-group">
            <label>Test Name (Optional):</label>
            <input type="text" id="pcTestName" placeholder="e.g., Peak Load Test">
        </div>
        
        <button class="btn btn-success" onclick="fetchPCResults()">
            🔍 Fetch Test Results
        </button>
        
        <div id="pcFetchStatus" style="display: none; margin-top: 15px;"></div>
    </div>
    
    <!-- Test Status Section -->
    <div class="appd-section" id="pcStatusSection" style="display: none;">
        <h3>📊 Test Status</h3>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #667eea;">
                <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">Test Status</div>
                <div style="font-weight: bold; font-size: 1.1em;" id="pcTestStatus">--</div>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #667eea;">
                <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">Collation Status</div>
                <div style="font-weight: bold; font-size: 1.1em;" id="pcCollationStatus">--</div>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #28a745;">
                <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">Passed</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #28a745;" id="pcPassedCount">--</div>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #dc3545;">
                <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">Failed</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #dc3545;" id="pcFailedCount">--</div>
            </div>
        </div>
    </div>
    
    <!-- Transaction Results -->
    <div class="appd-section" id="pcResultsSection" style="display: none;">
        <h3>📈 Transaction Results</h3>
        
        <div style="overflow-x: auto; margin-top: 15px;">
            <table id="pcTransactionsTable" style="width: 100%; border-collapse: collapse; background: white; border-radius: 6px; overflow: hidden;">
                <thead>
                    <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                        <th style="padding: 12px; text-align: left;">Transaction Name</th>
                        <th style="padding: 12px; text-align: right;">Min (s)</th>
                        <th style="padding: 12px; text-align: right;">Avg (s)</th>
                        <th style="padding: 12px; text-align: right;">Max (s)</th>
                        <th style="padding: 12px; text-align: right;">90th %ile</th>
                        <th style="padding: 12px; text-align: right;">Std Dev</th>
                        <th style="padding: 12px; text-align: right;">Pass %</th>
                        <th style="padding: 12px; text-align: center;">Status</th>
                    </tr>
                </thead>
                <tbody id="pcTransactionsBody">
                </tbody>
            </table>
        </div>
    </div>
</div>
```

---

## 📝 INCREMENTAL CHANGE #3: Add JavaScript Functions for AWR Tab

**File:** `index.html`  
**Location:** Inside `<script>` tag, add these functions

**ADD THESE FUNCTIONS:**
```javascript
// ==========================================
// AWR Analysis Functions
// ==========================================

async function uploadAWRReport() {
    const pcRunId = document.getElementById('awrPcRunId').value.trim();
    const dbName = document.getElementById('awrDatabaseName').value.trim();
    const testName = document.getElementById('awrTestName').value.trim();
    const fileInput = document.getElementById('awrFileInput');
    
    if (!pcRunId || !dbName || !fileInput.files.length) {
        alert('Please fill in all required fields and select a file');
        return;
    }
    
    const statusDiv = document.getElementById('awrUploadStatus');
    statusDiv.style.display = 'block';
    statusDiv.className = 'alert alert-info';
    statusDiv.innerHTML = '⏳ Uploading and analyzing AWR report...';
    
    try {
        // Generate master run ID
        const now = new Date();
        const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
        const runId = `RUNID_${pcRunId}_${dateStr}_001`;
        
        // Create form data
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('run_id', runId);
        formData.append('pc_run_id', pcRunId);
        formData.append('database_name', dbName);
        formData.append('lob_name', selectedLOB || 'Unknown');
        formData.append('test_name', testName);
        
        const response = await fetch('/api/v1/monitoring/awr/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.className = 'alert alert-success';
            statusDiv.innerHTML = `
                ✓ AWR Analysis Completed!<br>
                <strong>Run ID:</strong> ${data.run_id}<br>
                <strong>Database:</strong> ${data.database_name} (${data.instance_name})<br>
                <strong>Concerns Found:</strong> ${data.total_concerns} 
                (${data.critical_concerns} critical, ${data.warning_concerns} warnings)
            `;
            
            // Display results
            displayAWRResults(data);
            
            // Clear form
            fileInput.value = '';
            document.getElementById('awrPcRunId').value = '';
            document.getElementById('awrDatabaseName').value = '';
            document.getElementById('awrTestName').value = '';
            
        } else {
            statusDiv.className = 'alert alert-error';
            statusDiv.innerHTML = '✗ Error: ' + (data.message || 'Failed to analyze report');
        }
        
    } catch (error) {
        statusDiv.className = 'alert alert-error';
        statusDiv.innerHTML = '✗ Error: ' + error.message;
    }
}

function displayAWRResults(data) {
    // Show results section
    document.getElementById('awrResultsSection').style.display = 'block';
    
    // Update badge
    const badge = document.getElementById('awrResultsBadge');
    if (data.critical_concerns > 0) {
        badge.className = 'session-status failed';
        badge.textContent = 'Critical Issues Found';
    } else if (data.warning_concerns > 0) {
        badge.className = 'session-status running';
        badge.textContent = 'Warnings Found';
    } else {
        badge.className = 'session-status running';
        badge.textContent = 'Analysis Complete';
    }
    
    // Update summary cards
    document.getElementById('awrDbName').textContent = `${data.database_name} (${data.instance_name})`;
    document.getElementById('awrSnapRange').textContent = `${data.snapshot_begin} → ${data.snapshot_end}`;
    document.getElementById('awrElapsed').textContent = `${data.elapsed_time_minutes.toFixed(1)} min`;
    
    // Update concern counts
    document.getElementById('awrCriticalCount').textContent = data.critical_concerns;
    document.getElementById('awrWarningCount').textContent = data.warning_concerns;
    document.getElementById('awrInfoCount').textContent = data.total_concerns - data.critical_concerns - data.warning_concerns;
    
    // Display concerns
    const container = document.getElementById('awrConcernsContainer');
    
    if (data.concerns.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #28a745; padding: 20px;">✓ No performance concerns found!</p>';
        return;
    }
    
    let html = '<h4 style="margin-bottom: 15px;">Performance Concerns:</h4>';
    
    data.concerns.forEach(concern => {
        const severityClass = concern.severity.toLowerCase();
        
        html += `
            <div class="concern-item ${severityClass}">
                <div class="concern-header">
                    <div class="concern-title">${concern.title}</div>
                    <span class="concern-severity-badge ${severityClass}">${concern.severity}</span>
                </div>
                <div class="concern-description">${concern.description}</div>
        `;
        
        // Add metrics if available
        if (concern.metric_name && concern.metric_value !== null) {
            html += `
                <div class="concern-metrics">
                    <div class="concern-metric">
                        <div class="metric-value">${concern.metric_value.toFixed(2)}</div>
                        <div class="metric-label">${concern.metric_name}</div>
                    </div>
                    ${concern.threshold_value !== null ? `
                    <div class="concern-metric">
                        <div class="metric-value">${concern.threshold_value.toFixed(2)}</div>
                        <div class="metric-label">Threshold</div>
                    </div>
                    ` : ''}
                </div>
            `;
        }
        
        // Add recommendation
        html += `
                <div class="concern-recommendation">
                    <strong>💡 Recommendation:</strong><br>
                    ${concern.recommendation}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Scroll to results
    document.getElementById('awrResultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
}
```

**Continue to next part...**