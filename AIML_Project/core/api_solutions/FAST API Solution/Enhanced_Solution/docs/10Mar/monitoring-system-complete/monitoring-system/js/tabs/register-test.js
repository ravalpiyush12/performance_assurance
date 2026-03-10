// ==========================================
// REGISTER TEST TAB
// ==========================================

function getRegisterTestHTML() {
    return `
        <h2>📝 Register Test Run</h2>
        
        <div class="form-grid">
            <div class="form-group">
                <label for="pcRunId">PC Run ID <span class="required">*</span></label>
                <input type="text" id="pcRunId" placeholder="5-digit PC run ID" maxlength="5">
            </div>
            
            <div class="form-group">
                <label for="regLob">LOB <span class="required">*</span></label>
                <select id="regLob">
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
                <label for="testName">Test Name</label>
                <input type="text" id="testName" placeholder="e.g., Peak Load Test">
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="registerNewTest()">✓ Register Test Run</button>
        
        <div id="registrationStatus" style="margin-top: 20px;"></div>
        
        <div class="recent-tests">
            <h3>🕐 Recent Test Registrations</h3>
            <div id="recentRegistrations">
                <div class="loading">Loading...</div>
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
    
    lobSelect.value = STATE.currentLOB;
    updateTracks('regLob', 'regTrack');
    loadRecentRegistrations();
    
    lobSelect.addEventListener('change', () => updateTracks('regLob', 'regTrack'));
}

function updateTracks(lobSelectId, trackSelectId) {
    const lob = document.getElementById(lobSelectId).value;
    const trackSelect = document.getElementById(trackSelectId);
    
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
    const lob = document.getElementById('regLob').value;
    const track = document.getElementById('regTrack').value;
    const testName = document.getElementById('testName').value.trim();
    
    if (!validatePCRunId(pcRunId)) {
        showError('registrationStatus', 'PC Run ID must be 5 digits');
        return;
    }
    
    if (!lob) {
        showError('registrationStatus', 'Please select LOB');
        return;
    }
    
    showLoading('registrationStatus', 'Registering...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/pc/test-run/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                pc_run_id: pcRunId,
                lob_name: lob,
                track: track || null,
                test_name: testName || null
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            STATE.currentTestRun = { run_id: data.run_id, pc_run_id: pcRunId, lob_name: lob, track: track };
            showSuccess('registrationStatus', `✓ Test registered! Master Run ID: ${data.run_id}`);
            
            document.getElementById('pcRunId').value = '';
            document.getElementById('testName').value = '';
            loadRecentRegistrations();
        } else {
            showError('registrationStatus', data.detail || 'Registration failed');
        }
    } catch (error) {
        showError('registrationStatus', error.message);
    }
}

async function loadRecentRegistrations() {
    showLoading('recentRegistrations', 'Loading...');
    
    try {
        const response = await Auth.authenticatedFetch(
            `${CONFIG.API_BASE}/monitoring/pc/test-run/recent?lob_name=${STATE.currentLOB}`
        );
        const data = await response.json();
        
        if (response.ok && data.success) {
            const runs = data.runs || [];
            
            if (runs.length === 0) {
                document.getElementById('recentRegistrations').innerHTML = '<p>No recent registrations</p>';
                return;
            }
            
            let html = '';
            runs.forEach(run => {
                html += `
                    <div class="test-item">
                        <div><strong>Run ID:</strong> ${run.run_id}</div>
                        <div><strong>PC Run ID:</strong> ${run.pc_run_id}</div>
                        <div><strong>LOB:</strong> ${run.lob_name} ${run.track ? '| Track: ' + run.track : ''}</div>
                        <div><strong>Registered:</strong> ${formatDateTime(run.created_date)}</div>
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
