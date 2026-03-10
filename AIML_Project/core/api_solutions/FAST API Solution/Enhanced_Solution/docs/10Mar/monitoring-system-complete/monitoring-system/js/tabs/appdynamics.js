// ==========================================
// APPDYNAMICS TAB (3 sub-tabs)
// ==========================================

function getAppDynamicsHTML() {
    return `
        <h2>📊 AppDynamics Monitoring</h2>
        
        <div class="sub-tabs">
            <button class="sub-tab active" onclick="switchSubTab(event, 'appdDiscovery')">🔍 Discovery</button>
            <button class="sub-tab" onclick="switchSubTab(event, 'appdHealth')">✅ Health Check</button>
            <button class="sub-tab" onclick="switchSubTab(event, 'appdMonitoring')">▶️ Start Monitoring</button>
        </div>
        
        <div id="appdDiscovery" class="sub-tab-content active">
            <h3>🔍 AppDynamics Discovery</h3>
            <div class="form-grid">
                <div class="form-group">
                    <label>LOB Name</label>
                    <select id="discoveryLob">
                        <option value="">-- Select LOB --</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Track</label>
                    <select id="discoveryTrack">
                        <option value="">-- Select Track --</option>
                    </select>
                </div>
            </div>
            <button class="btn btn-primary" onclick="runDiscovery()">🔄 Run Discovery & Save Config</button>
            <div id="discoveryResults" style="margin-top: 20px;"></div>
        </div>
        
        <div id="appdHealth" class="sub-tab-content">
            <h3>✅ Health Check</h3>
            <div class="form-grid">
                <div class="form-group">
                    <label>LOB Name</label>
                    <select id="healthLob">
                        <option value="">-- Select LOB --</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Track</label>
                    <select id="healthTrack">
                        <option value="">-- Select Track --</option>
                    </select>
                </div>
            </div>
            <button class="btn btn-refresh" onclick="checkHealth()">🔄 Refresh Health Status</button>
            <div id="healthResults" style="margin-top: 20px;"></div>
        </div>
        
        <div id="appdMonitoring" class="sub-tab-content">
            <h3>▶️ Start Monitoring</h3>
            <div class="form-grid">
                <div class="form-group">
                    <label>LOB Name</label>
                    <select id="monitorLob">
                        <option value="">-- Select LOB --</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Track</label>
                    <select id="monitorTrack">
                        <option value="">-- Select Track --</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Duration</label>
                    <select id="monitorDuration">
                        <option value="300">5 minutes</option>
                        <option value="600">10 minutes</option>
                        <option value="1200">20 minutes</option>
                        <option value="2400">40 minutes</option>
                        <option value="">Run until manually stopped</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>PC Run ID (for correlation)</label>
                    <input type="text" id="monitorPcRunId" placeholder="5-digit run ID">
                </div>
            </div>
            <button class="btn btn-primary" onclick="startMonitoring()">▶️ Start Monitoring</button>
            <div id="monitoringStatus" style="margin-top: 20px;"></div>
            
            <div class="active-sessions-section" style="margin-top: 30px;">
                <h4>📊 Active Monitoring Sessions</h4>
                <div id="activeSessions"><p>No active sessions</p></div>
            </div>
        </div>
    `;
}

function init_appdynamics() {
    ['discoveryLob', 'healthLob', 'monitorLob'].forEach(id => {
        const select = document.getElementById(id);
        Object.keys(CONFIG.LOB_MONITORING_MAP).forEach(lob => {
            const option = document.createElement('option');
            option.value = lob;
            option.textContent = lob;
            select.appendChild(option);
        });
        select.value = STATE.currentLOB;
    });
    
    // LOB change handlers
    document.getElementById('discoveryLob').addEventListener('change', () => updateTracks('discoveryLob', 'discoveryTrack'));
    document.getElementById('healthLob').addEventListener('change', () => updateTracks('healthLob', 'healthTrack'));
    document.getElementById('monitorLob').addEventListener('change', () => updateTracks('monitorLob', 'monitorTrack'));
    
    // Initialize tracks
    updateTracks('discoveryLob', 'discoveryTrack');
    updateTracks('healthLob', 'healthTrack');
    updateTracks('monitorLob', 'monitorTrack');
}

async function runDiscovery() {
    const lob = document.getElementById('discoveryLob').value;
    const track = document.getElementById('discoveryTrack').value;
    
    if (!lob) {
        showError('discoveryResults', 'Please select LOB');
        return;
    }
    
    showLoading('discoveryResults', 'Running discovery...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/appd/discovery/run`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ lob_name: lob, track: track || null })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSuccess('discoveryResults', `✓ Discovery completed! Found ${data.applications_count || 0} applications`);
        } else {
            showError('discoveryResults', data.detail || 'Discovery failed');
        }
    } catch (error) {
        showError('discoveryResults', error.message);
    }
}

async function checkHealth() {
    const lob = document.getElementById('healthLob').value;
    const track = document.getElementById('healthTrack').value;
    
    if (!lob) {
        showError('healthResults', 'Please select LOB');
        return;
    }
    
    showLoading('healthResults', 'Checking health...');
    
    try {
        const response = await Auth.authenticatedFetch(
            `${CONFIG.API_BASE}/monitoring/appd/health?lob_name=${lob}${track ? '&track=' + track : ''}`
        );
        const data = await response.json();
        
        if (response.ok && data.success) {
            const status = data.status || 'unknown';
            const statusClass = status === 'healthy' ? 'alert-success' : 'alert-warning';
            document.getElementById('healthResults').innerHTML = `
                <div class="alert ${statusClass}">
                    <strong>Status:</strong> ${status.toUpperCase()}
                </div>
            `;
        } else {
            showError('healthResults', data.detail || 'Health check failed');
        }
    } catch (error) {
        showError('healthResults', error.message);
    }
}

async function startMonitoring() {
    const lob = document.getElementById('monitorLob').value;
    const track = document.getElementById('monitorTrack').value;
    const duration = document.getElementById('monitorDuration').value;
    const pcRunId = document.getElementById('monitorPcRunId').value.trim();
    
    if (!lob) {
        showError('monitoringStatus', 'Please select LOB');
        return;
    }
    
    showLoading('monitoringStatus', 'Starting monitoring...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/appd/monitoring/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                lob_name: lob,
                track: track || null,
                duration_seconds: duration ? parseInt(duration) : null,
                pc_run_id: pcRunId || null
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSuccess('monitoringStatus', `✓ Monitoring started! Session ID: ${data.session_id}`);
            loadActiveSessions();
        } else {
            showError('monitoringStatus', data.detail || 'Failed to start monitoring');
        }
    } catch (error) {
        showError('monitoringStatus', error.message);
    }
}

async function loadActiveSessions() {
    try {
        const response = await Auth.authenticatedFetch(
            `${CONFIG.API_BASE}/monitoring/appd/sessions/active?lob_name=${STATE.currentLOB}`
        );
        const data = await response.json();
        
        if (response.ok && data.success) {
            const sessions = data.sessions || [];
            
            if (sessions.length === 0) {
                document.getElementById('activeSessions').innerHTML = '<p>No active sessions</p>';
                return;
            }
            
            let html = '';
            sessions.forEach(session => {
                html += `
                    <div class="session-item">
                        <div><strong>Session ID:</strong> ${session.session_id}</div>
                        <div><strong>LOB:</strong> ${session.lob_name} ${session.track ? '| Track: ' + session.track : ''}</div>
                        <div><strong>Status:</strong> ${session.status}</div>
                    </div>
                `;
            });
            
            document.getElementById('activeSessions').innerHTML = html;
        }
    } catch (error) {
        console.error('Failed to load active sessions:', error);
    }
}
