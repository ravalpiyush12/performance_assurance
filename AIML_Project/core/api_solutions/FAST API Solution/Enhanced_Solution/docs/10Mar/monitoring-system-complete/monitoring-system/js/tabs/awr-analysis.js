// ==========================================
// AWR ANALYSIS TAB
// ==========================================

function getAWRHTML() {
    return `
        <h2>📉 AWR Analysis - Upload & Analyze</h2>
        
        <div class="form-grid">
            <div class="form-group">
                <label>AWR HTML File <span class="required">*</span></label>
                <input type="file" id="awrFile" accept=".html,.htm">
            </div>
            
            <div class="form-group">
                <label>PC Run ID <span class="required">*</span></label>
                <input type="text" id="awrPcRunId" placeholder="5-digit run ID" maxlength="5">
            </div>
            
            <div class="form-group">
                <label>Database Name</label>
                <select id="awrDatabaseName">
                    <option value="">-- Select Database --</option>
                </select>
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="uploadAWR()">📤 Upload AWR Report</button>
        
        <div id="awrUploadStatus" style="margin-top: 20px;"></div>
    `;
}

function init_awr() {
    const dbSelect = document.getElementById('awrDatabaseName');
    CONFIG.DATABASES.forEach(db => {
        const option = document.createElement('option');
        option.value = db;
        option.textContent = db;
        dbSelect.appendChild(option);
    });
}

async function uploadAWR() {
    const file = document.getElementById('awrFile').files[0];
    const pcRunId = document.getElementById('awrPcRunId').value.trim();
    const dbName = document.getElementById('awrDatabaseName').value;
    
    if (!file) {
        showError('awrUploadStatus', 'Please select AWR file');
        return;
    }
    
    if (!validatePCRunId(pcRunId)) {
        showError('awrUploadStatus', 'PC Run ID must be 5 digits');
        return;
    }
    
    showLoading('awrUploadStatus', 'Uploading AWR report...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('pc_run_id', pcRunId);
        if (dbName) formData.append('database_name', dbName);
        
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/awr/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSuccess('awrUploadStatus', `✓ AWR report uploaded and analyzed successfully!`);
            document.getElementById('awrFile').value = '';
            document.getElementById('awrPcRunId').value = '';
        } else {
            showError('awrUploadStatus', data.detail || 'Upload failed');
        }
    } catch (error) {
        showError('awrUploadStatus', error.message);
    }
}
