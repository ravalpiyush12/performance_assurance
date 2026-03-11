// ==========================================
// PERFORMANCE CENTER TAB - Complete Implementation
// Based on original index.html working code
// ==========================================

function getPerformanceCenterHTML() {
    return `
        <h2>⚡ Performance Center Test Analysis</h2>
        <p style="color:#666;margin-bottom:20px;">
            Fetch and analyze Performance Center test results, transaction data, and statistics.
        </p>
        
        <div class="form-grid">
            <div class="form-group">
                <label for="pcAnalysisRunId">PC Run ID <span class="required">*</span></label>
                <input type="text" id="pcAnalysisRunId" placeholder="5-digit run ID" maxlength="5">
                <small>Performance Center run ID to analyze</small>
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="fetchPCResults()">📊 Fetch Test Results</button>
        
        <div id="pcResults" style="margin-top:20px;"></div>
        
        <!-- Test Status Section -->
        <div id="pcTestStatus" style="margin-top:30px;"></div>
        
        <!-- Transaction Results -->
        <div id="pcTransactions" style="margin-top:30px;"></div>
    `;
}

function init_pc() {
    // Initialize if needed
}

async function fetchPCResults() {
    const runId = document.getElementById('pcAnalysisRunId').value.trim();
    
    if (!runId) {
        showError('pcResults', '⚠ Please enter PC Run ID');
        return;
    }
    
    if (!validatePCRunId(runId)) {
        showError('pcResults', '⚠ PC Run ID must be exactly 5 digits');
        return;
    }
    
    showLoading('pcResults', 'Fetching Performance Center test results...');
    showLoading('pcTestStatus', '');
    showLoading('pcTransactions', '');
    
    try {
        const response = await Auth.authenticatedFetch(
            `${CONFIG.API_BASE}/monitoring/pc/results/${runId}`
        );
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Main Status
            const statusHTML = `
                <div class="alert alert-success">
                    <strong>✓ Test results retrieved successfully!</strong><br>
                    <strong>PC Run ID:</strong> ${runId}<br>
                    ${data.run_id ? `<strong>Master RUN_ID:</strong> ${data.run_id}<br>` : ''}
                    <strong>Status:</strong> ${data.status || 'N/A'}
                </div>
            `;
            document.getElementById('pcResults').innerHTML = statusHTML;
            
            // Test Statistics
            const stats = data.statistics || {};
            let statsHTML = '<h3>📊 Test Statistics</h3>';
            statsHTML += '<div class="stat-grid">';
            
            if (stats.duration) {
                statsHTML += `
                    <div class="stat-card">
                        <h4>Duration</h4>
                        <div class="value">${stats.duration}</div>
                    </div>
                `;
            }
            
            if (stats.vusers) {
                statsHTML += `
                    <div class="stat-card">
                        <h4>Virtual Users</h4>
                        <div class="value">${stats.vusers}</div>
                    </div>
                `;
            }
            
            if (stats.passed_transactions) {
                statsHTML += `
                    <div class="stat-card">
                        <h4>Passed</h4>
                        <div class="value" style="color:#4caf50;">${stats.passed_transactions}</div>
                    </div>
                `;
            }
            
            if (stats.failed_transactions) {
                statsHTML += `
                    <div class="stat-card">
                        <h4>Failed</h4>
                        <div class="value" style="color:#f44336;">${stats.failed_transactions}</div>
                    </div>
                `;
            }
            
            if (stats.average_response_time) {
                statsHTML += `
                    <div class="stat-card">
                        <h4>Avg Response Time</h4>
                        <div class="value">${stats.average_response_time}s</div>
                    </div>
                `;
            }
            
            statsHTML += '</div>';
            document.getElementById('pcTestStatus').innerHTML = statsHTML;
            
            // Transaction Details
            const transactions = data.transactions || [];
            if (transactions.length > 0) {
                let transHTML = '<h3>📋 Transaction Details</h3>';
                transHTML += '<div style="overflow-x:auto;">';
                transHTML += '<table style="width:100%;border-collapse:collapse;">';
                transHTML += `
                    <thead>
                        <tr style="background:#f5f5f5;text-align:left;">
                            <th style="padding:10px;border:1px solid #ddd;">Transaction Name</th>
                            <th style="padding:10px;border:1px solid #ddd;">Count</th>
                            <th style="padding:10px;border:1px solid #ddd;">Avg Response</th>
                            <th style="padding:10px;border:1px solid #ddd;">Min</th>
                            <th style="padding:10px;border:1px solid #ddd;">Max</th>
                            <th style="padding:10px;border:1px solid #ddd;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                `;
                
                transactions.forEach(txn => {
                    const statusColor = txn.status === 'Passed' ? '#4caf50' : '#f44336';
                    transHTML += `
                        <tr>
                            <td style="padding:10px;border:1px solid #ddd;">${txn.name}</td>
                            <td style="padding:10px;border:1px solid #ddd;">${txn.count || 0}</td>
                            <td style="padding:10px;border:1px solid #ddd;">${txn.avg_response || 'N/A'}</td>
                            <td style="padding:10px;border:1px solid #ddd;">${txn.min_response || 'N/A'}</td>
                            <td style="padding:10px;border:1px solid #ddd;">${txn.max_response || 'N/A'}</td>
                            <td style="padding:10px;border:1px solid #ddd;">
                                <span style="color:${statusColor};font-weight:600;">${txn.status}</span>
                            </td>
                        </tr>
                    `;
                });
                
                transHTML += '</tbody></table></div>';
                document.getElementById('pcTransactions').innerHTML = transHTML;
            } else {
                document.getElementById('pcTransactions').innerHTML = 
                    '<p style="color:#999;text-align:center;padding:20px;">No transaction data available</p>';
            }
            
        } else {
            showError('pcResults', data.detail || 'Failed to fetch test results');
            document.getElementById('pcTestStatus').innerHTML = '';
            document.getElementById('pcTransactions').innerHTML = '';
        }
    } catch (error) {
        showError('pcResults', error.message);
        document.getElementById('pcTestStatus').innerHTML = '';
        document.getElementById('pcTransactions').innerHTML = '';
    }
}
