// ==========================================
// AWR ANALYSIS TAB - Complete Implementation
// Based on original index.html working code
// ==========================================

function getAWRHTML() {
    return `
        <h2>📉 AWR Analysis - Upload & Analyze Oracle Reports</h2>
        <p style="color:#666;margin-bottom:20px;">
            Upload AWR HTML reports for automated performance analysis. Reports are linked to PC Run ID.
        </p>
        
        <div class="form-grid">
            <div class="form-group">
                <label for="awrFile">AWR HTML File <span class="required">*</span></label>
                <input type="file" id="awrFile" accept=".html,.htm">
                <small>Upload Oracle AWR HTML report to analyze database performance</small>
            </div>
            
            <div class="form-group">
                <label for="awrPcRunId">PC Run ID <span class="required">*</span></label>
                <input type="text" id="awrPcRunId" placeholder="5-digit run ID" maxlength="5">
                <small>Performance Center run ID to link this report</small>
            </div>
            
            <div class="form-group">
                <label for="awrDatabaseName">Database Name</label>
                <select id="awrDatabaseName">
                    <option value="">-- Select Database --</option>
                </select>
                <small>Optional: Specify database if report doesn't contain DB info</small>
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="uploadAWR()">📤 Upload & Analyze AWR Report</button>
        
        <div id="awrUploadStatus" style="margin-top:20px;"></div>
    `;
}

function init_awr() {
    // Populate database dropdown
    const dbSelect = document.getElementById('awrDatabaseName');
    CONFIG.DATABASES.forEach(db => {
        const option = document.createElement('option');
        option.value = db;
        option.textContent = db;
        dbSelect.appendChild(option);
    });
}

async function uploadAWR() {
    const fileInput = document.getElementById('awrFile');
    const file = fileInput.files[0];
    const pcRunId = document.getElementById('awrPcRunId').value.trim();
    const dbName = document.getElementById('awrDatabaseName').value;
    
    // Validation
    if (!file) {
        showError('awrUploadStatus', '⚠ Please select an AWR HTML file');
        return;
    }
    
    if (!pcRunId) {
        showError('awrUploadStatus', '⚠ Please enter PC Run ID');
        return;
    }
    
    if (!validatePCRunId(pcRunId)) {
        showError('awrUploadStatus', '⚠ PC Run ID must be exactly 5 digits');
        return;
    }
    
    showLoading('awrUploadStatus', 'Uploading and analyzing AWR report... This may take a moment.');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('pc_run_id', pcRunId);
        if (dbName) {
            formData.append('database_name', dbName);
        }
        
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/awr/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const successHTML = `
                <div class="alert alert-success">
                    <strong>✓ AWR Report uploaded and analyzed successfully!</strong><br>
                    <strong>PC Run ID:</strong> ${pcRunId}<br>
                    ${data.database_name ? `<strong>Database:</strong> ${data.database_name}<br>` : ''}
                    ${data.run_id ? `<strong>Linked to Master RUN_ID:</strong> ${data.run_id}<br>` : ''}
                    <small>Report data has been stored in Oracle database for performance analysis</small>
                </div>
            `;
            document.getElementById('awrUploadStatus').innerHTML = successHTML;
            
            // Clear form
            fileInput.value = '';
            document.getElementById('awrPcRunId').value = '';
            document.getElementById('awrDatabaseName').value = '';
            
        } else {
            showError('awrUploadStatus', data.detail || 'Upload failed');
        }
    } catch (error) {
        showError('awrUploadStatus', error.message);
    }
}
