// ==========================================
// PERFORMANCE CENTER TAB
// ==========================================

function getPerformanceCenterHTML() {
    return `
        <h2>⚡ Performance Center Analysis</h2>
        
        <div class="form-grid">
            <div class="form-group">
                <label>PC Run ID <span class="required">*</span></label>
                <input type="text" id="pcAnalysisRunId" placeholder="5-digit run ID" maxlength="5">
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="fetchPCResults()">📊 Fetch Test Results</button>
        
        <div id="pcResults" style="margin-top: 20px;"></div>
    `;
}

function init_pc() {
    // Initialize if needed
}

async function fetchPCResults() {
    const runId = document.getElementById('pcAnalysisRunId').value.trim();
    
    if (!validatePCRunId(runId)) {
        showError('pcResults', 'PC Run ID must be 5 digits');
        return;
    }
    
    showLoading('pcResults', 'Fetching results...');
    
    try {
        const response = await Auth.authenticatedFetch(
            `${CONFIG.API_BASE}/monitoring/pc/results/${runId}`
        );
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            let html = '<div class="alert alert-success">✓ Test results retrieved</div>';
            html += `<div class="stat-grid">`;
            html += `<div class="stat-card"><h4>Status</h4><div class="value">${data.status || 'N/A'}</div></div>`;
            html += `<div class="stat-card"><h4>Duration</h4><div class="value">${data.duration || 'N/A'}</div></div>`;
            html += `<div class="stat-card"><h4>Users</h4><div class="value">${data.vusers || 'N/A'}</div></div>`;
            html += `</div>`;
            
            document.getElementById('pcResults').innerHTML = html;
        } else {
            showError('pcResults', data.detail || 'Failed to fetch results');
        }
    } catch (error) {
        showError('pcResults', error.message);
    }
}
