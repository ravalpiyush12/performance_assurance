// ==========================================
// REGISTER TEST TAB - FIXED VERSION
// Ensures proper initialization on tab load
// ==========================================

function getRegisterTestHTML() {
    return `
        <h2>📝 Register Test Run</h2>
        <p style="color: #666; margin-bottom: 20px;">
            Fill in the Performance Center test run details. You'll get a Master RUN_ID for monitoring.
        </p>
        
        <div class="form-grid">
            <div class="form-group">
                <label for="pcRunId">PC Run ID <span class="required">*</span></label>
                <input type="text" id="pcRunId" placeholder="5-digit run ID" maxlength="5">
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
            <p style="color: #666; font-size: 14px;">
                Tests found/only tests (data already filters for active tests)
            </p>
            <button class="btn btn-refresh" onclick="loadRecentRegistrations()" style="margin-bottom: 15px;">
                🔄 Refresh
            </button>
            <div id="recentRegistrations">
                <div class="loading">Loading recent registrations...</div>
            </div>
        </div>
    `;
}

function init_registerTest() {
    console.log('🔧 Initializing Register Test tab...');
    
    // Populate LOB dropdown
    const lobSelect = document.getElementById('regLob');
    if (!lobSelect) {
        console.error('❌ regLob select not found!');
        return;
    }
    
    // Clear existing options except first one
    lobSelect.innerHTML = '<option value="">-- Select LOB --</option>';
    
    // Add all LOBs from config
    Object.keys(CONFIG.LOB_MONITORING_MAP).forEach(lob => {
        const option = document.createElement('option');
        option.value = lob;
        option.textContent = lob;
        lobSelect.appendChild(option);
    });
    
    console.log('✓ LOB dropdown populated with', Object.keys(CONFIG.LOB_MONITORING_MAP).length, 'LOBs');
    
    // Pre-select current LOB if available
    if (STATE.currentLOB) {
        lobSelect.value = STATE.currentLOB;
        console.log('✓ Pre-selected LOB:', STATE.currentLOB);
        onRegLobChange();
    }
    
    // Load recent registrations automatically
    console.log('🔄 Loading recent registrations...');
    loadRecentRegistrations();
}

function onRegLobChange() {
    const lob = document.getElementById('regLob').value;
    const trackSelect = document.getElementById('regTrack');
    
    if (!trackSelect) {
        console.error('❌ regTrack select not found!');
        return;
    }
    
    // Clear tracks
    trackSelect.innerHTML = '<option value="">-- Select Track --</option>';
    
    // Populate tracks if LOB has tracks configured
    if (lob && CONFIG.TRACKS && CONFIG.TRACKS[lob]) {
        CONFIG.TRACKS[lob].forEach(track => {
            const option = document.createElement('option');
            option.value = track;
            option.textContent = track;
            trackSelect.appendChild(option);
        });
        console.log('✓ Tracks populated for', lob, ':', CONFIG.TRACKS[lob].length, 'tracks');
    }
}

async function registerNewTest() {
    const pcRunId = document.getElementById('pcRunId').value.trim();
    const lobName = document.getElementById('regLob').value;
    const track = document.getElementById('regTrack').value;
    const testName = document.getElementById('testName').value.trim();
    
    console.log('📝 Attempting to register test:', { pcRunId, lobName, track, testName });
    
    // Validation
    if (!pcRunId) {
        showError('registrationStatus', '⚠ Please enter PC Run ID');
        return;
    }
    
    if (!validatePCRunId(pcRunId)) {
        showError('registrationStatus', '⚠ PC Run ID must be exactly 5 digits');
        return;
    }
    
    if (!lobName) {
        showError('registrationStatus', '⚠ Please select LOB');
        return;
    }
    
    showLoading('registrationStatus', 'Registering test run...');
    
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
        console.log('📊 Registration response:', data);
        
        if (response.ok && data.success) {
            // Store in global state
            STATE.currentTestRun = {
                run_id: data.run_id,
                pc_run_id: pcRunId,
                lob_name: lobName,
                track: track
            };
            
            // Success message
            const successHTML = `
                <div class="alert alert-success">
                    <strong>✓ Test Registered Successfully!</strong><br>
                    <strong>Master RUN_ID:</strong> <span style="font-size: 18px; color: #2e7d32;">${data.run_id}</span><br>
                    <strong>PC Run ID:</strong> ${pcRunId}<br>
                    <strong>LOB:</strong> ${lobName}${track ? ' | Track: ' + track : ''}
                </div>
            `;
            document.getElementById('registrationStatus').innerHTML = successHTML;
            
            // Clear form
            document.getElementById('pcRunId').value = '';
            document.getElementById('testName').value = '';
            
            console.log('✓ Test registered successfully:', data.run_id);
            
            // Reload recent registrations after 1 second
            setTimeout(() => {
                console.log('🔄 Reloading recent registrations...');
                loadRecentRegistrations();
            }, 1000);
            
        } else {
            console.error('❌ Registration failed:', data);
            showError('registrationStatus', data.detail || data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('❌ Registration error:', error);
        showError('registrationStatus', 'Error: ' + error.message);
    }
}

async function loadRecentRegistrations() {
    const selectedLob = document.getElementById('regLob').value || STATE.currentLOB;
    
    console.log('📋 Loading recent registrations for LOB:', selectedLob);
    
    if (!selectedLob) {
        document.getElementById('recentRegistrations').innerHTML = 
            '<p class="alert alert-info">Please select a LOB to view recent registrations</p>';
        return;
    }
    
    showLoading('recentRegistrations', 'Loading recent registrations...');
    
    try {
        const url = `${CONFIG.API_BASE}/monitoring/pc/test-run/recent?lob_name=${encodeURIComponent(selectedLob)}`;
        console.log('🔗 Fetching:', url);
        
        const response = await Auth.authenticatedFetch(url);
        const data = await response.json();
        
        console.log('📊 Recent registrations response:', data);
        
        if (response.ok && data.success) {
            const runs = data.runs || data.test_runs || [];
            console.log('✓ Found', runs.length, 'registrations');
            
            if (runs.length === 0) {
                document.getElementById('recentRegistrations').innerHTML = 
                    '<p style="text-align:center;color:#999;padding:20px;">No recent registrations found for ' + selectedLob + '</p>';
                return;
            }
            
            // Build HTML
            let html = '';
            runs.forEach((run, index) => {
                const statusColor = run.test_status === 'COMPLETED' ? '#4caf50' : 
                                  run.test_status === 'RUNNING' ? '#ff9800' : 
                                  run.test_status === 'ANALYZING' ? '#2196f3' : '#667eea';
                
                html += `
                    <div class="test-item" style="border-left:4px solid ${statusColor};margin-bottom:10px;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div style="flex:1;">
                                <div style="font-size:16px;font-weight:600;margin-bottom:8px;">
                                    <strong>Master RUN_ID:</strong> 
                                    <span style="color:${statusColor};">${run.run_id}</span>
                                </div>
                                <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:8px;">
                                    <div><strong>PC Run ID:</strong> ${run.pc_run_id}</div>
                                    <div><strong>LOB:</strong> ${run.lob_name}</div>
                                    ${run.track ? `<div><strong>Track:</strong> ${run.track}</div>` : ''}
                                    ${run.test_name ? `<div><strong>Test Name:</strong> ${run.test_name}</div>` : ''}
                                </div>
                                <div style="font-size:12px;color:#666;">
                                    <strong>Registered:</strong> ${formatDateTime(run.created_date)}
                                </div>
                            </div>
                            <div>
                                <span style="padding:6px 12px;background:${statusColor};color:white;border-radius:4px;font-size:12px;font-weight:600;">
                                    ${run.test_status || 'INITIATED'}
                                </span>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            // Add summary
            const summary = `
                <div style="margin-bottom:15px;padding:10px;background:#f5f5f5;border-radius:6px;text-align:center;">
                    <strong>Total:</strong> ${runs.length} registrations | <strong>LOB:</strong> ${selectedLob}
                </div>
            `;
            
            document.getElementById('recentRegistrations').innerHTML = summary + html;
            console.log('✓ Recent registrations displayed successfully');
            
        } else {
            console.error('❌ Failed to load recent registrations:', data);
            showError('recentRegistrations', 'Failed to load recent registrations');
        }
    } catch (error) {
        console.error('❌ Error loading recent registrations:', error);
        showError('recentRegistrations', 'Error: ' + error.message);
    }
}

// Auto-initialize when tab becomes active
console.log('✓ Register Test tab JS loaded');