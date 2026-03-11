// ==========================================
// REGISTER TEST TAB - Complete Implementation
// Based on original index.html working code
// ==========================================

function getRegisterTestHTML() {
    return `
        <h2>📝 Register Test Run</h2>
        <p style="color: #666; margin-bottom: 20px;">
            Fill in the details of your Performance Center test run. You'll get a Master RUN_ID for monitoring.
        </p>
        
        <div class="form-grid">
            <div class="form-group">
                <label for="pcRunId">PC Run ID <span class="required">*</span></label>
                <input type="text" id="pcRunId" placeholder="e.g., 35787" maxlength="5">
                <small>5-digit Performance Center run ID</small>
            </div>
            
            <div class="form-group">
                <label for="regLob">LOB Name <span class="required">*</span></label>
                <select id="regLob" onchange="onRegLobChange()">
                    <option value="">-- Select LOB --</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="regTrack">Track</label>
                <select id="regTrack">
                    <option value="">-- Select Track --</option>
                </select>
                <small>Optional: Select track if applicable</small>
            </div>
            
            <div class="form-group">
                <label for="testName">Test Name (Optional)</label>
                <input type="text" id="testName" placeholder="e.g., Peak Load Test">
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="registerNewTest()">✓ Register Test Run</button>
        
        <div id="registrationStatus" style="margin-top: 20px;"></div>
        
        <div class="recent-tests" style="margin-top: 30px;">
            <h3>🕐 Recent Test Registrations</h3>
            <button class="btn btn-refresh" onclick="loadRecentRegistrations()">🔄 Refresh</button>
            <div id="recentRegistrations">
                <div class="loading">Click refresh to load...</div>
            </div>
        </div>
    `;
}

function init_registerTest() {
    const lobSelect = document.getElementById('regLob');
    Object.keys(CONFIG.LOB_MONITORING_MAP).forEach(lob => {
        const option = document.createElement('option');
        option.value = lob;
        option.textContent = lob;
        lobSelect.appendChild(option);
    });
    
    if (STATE.currentLOB) {
        lobSelect.value = STATE.currentLOB;
        onRegLobChange();
    }
}

function onRegLobChange() {
    const lob = document.getElementById('regLob').value;
    const trackSelect = document.getElementById('regTrack');
    
    trackSelect.innerHTML = '<option value="">-- Select Track --</option>';
    
    if (lob && CONFIG.TRACKS[lob]) {
        CONFIG.TRACKS[lob].forEach(track => {
            const option = document.createElement('option');
            option.value = track;
            option.textContent = track;
            trackSelect.appendChild(option);
        });
    }
}

async function registerNewTest() {
    const pcRunId = document.getElementById('pcRunId').value.trim();
    const lobName = document.getElementById('regLob').value;
    const track = document.getElementById('regTrack').value;
    const testName = document.getElementById('testName').value.trim();
    
    if (!pcRunId) {
        showError('registrationStatus', '⚠ Please enter PC Run ID');
        return;
    }
    
    if (!validatePCRunId(pcRunId)) {
        showError('registrationStatus', '⚠ PC Run ID must be 5 digits');
        return;
    }
    
    if (!lobName) {
        showError('registrationStatus', '⚠ Please select LOB');
        return;
    }
    
    showLoading('registrationStatus', 'Registering...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/pc/test-run/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                pc_run_id: pcRunId,
                lob_name: lobName,
                track: track || null,
                test_name: testName || null
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            STATE.currentTestRun = {
                run_id: data.run_id,
                pc_run_id: pcRunId,
                lob_name: lobName,
                track: track
            };
            
            const successHTML = `
                <div class="alert alert-success">
                    <strong>✓ Test Registered Successfully!</strong><br>
                    <strong>Master RUN_ID:</strong> <span style="font-size: 18px;">${data.run_id}</span><br>
                    <strong>PC Run ID:</strong> ${pcRunId}<br>
                    <strong>LOB:</strong> ${lobName}${track ? ' | Track: ' + track : ''}
                </div>
            `;
            document.getElementById('registrationStatus').innerHTML = successHTML;
            
            document.getElementById('pcRunId').value = '';
            document.getElementById('testName').value = '';
            
            setTimeout(() => loadRecentRegistrations(), 1000);
            
        } else {
            showError('registrationStatus', data.detail || 'Registration failed');
        }
    } catch (error) {
        showError('registrationStatus', error.message);
    }
}

async function loadRecentRegistrations() {
    const selectedLob = document.getElementById('regLob').value || STATE.currentLOB;
    
    if (!selectedLob) {
        document.getElementById('recentRegistrations').innerHTML = 
            '<p class="alert alert-info">Select LOB to view registrations</p>';
        return;
    }
    
    showLoading('recentRegistrations', 'Loading...');
    
    try {
        const response = await Auth.authenticatedFetch(
            `${CONFIG.API_BASE}/monitoring/pc/test-run/recent?lob_name=${encodeURIComponent(selectedLob)}`
        );
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const runs = data.runs || [];
            
            if (runs.length === 0) {
                document.getElementById('recentRegistrations').innerHTML = 
                    '<p style="text-align:center;color:#999;padding:20px;">No recent registrations</p>';
                return;
            }
            
            let html = '';
            runs.forEach(run => {
                const statusColor = run.test_status === 'COMPLETED' ? '#4caf50' : 
                                  run.test_status === 'RUNNING' ? '#ff9800' : '#667eea';
                
                html += `
                    <div class="test-item" style="border-left:4px solid ${statusColor};">
                        <div><strong>Master RUN_ID:</strong> <span style="color:${statusColor};">${run.run_id}</span></div>
                        <div><strong>PC Run ID:</strong> ${run.pc_run_id}</div>
                        <div><strong>LOB:</strong> ${run.lob_name}${run.track ? ' | Track: ' + run.track : ''}</div>
                        ${run.test_name ? `<div><strong>Test Name:</strong> ${run.test_name}</div>` : ''}
                        <div style="font-size:12px;color:#666;margin-top:5px;">
                            <strong>Registered:</strong> ${formatDateTime(run.created_date)}
                        </div>
                        <span style="float:right;padding:4px 8px;background:${statusColor};color:white;border-radius:4px;font-size:11px;">
                            ${run.test_status || 'INITIATED'}
                        </span>
                    </div>
                `;
            });
            
            document.getElementById('recentRegistrations').innerHTML = html;
            
        } else {
            showError('recentRegistrations', 'Failed to load');
        }
    } catch (error) {
        showError('recentRegistrations', error.message);
    }
}
