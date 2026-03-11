// ==========================================
// APPDYNAMICS TAB - Complete Implementation
// Based on original index.html working code
// 3 Sub-tabs: Discovery, Health Check, Start Monitoring
// ==========================================

function getAppDynamicsHTML() {
    return `
        <h2>📊 AppDynamics Monitoring</h2>
        
        <div class="sub-tabs">
            <button class="sub-tab active" onclick="switchSubTab(event, 'appdDiscovery')">🔍 Discovery</button>
            <button class="sub-tab" onclick="switchSubTab(event, 'appdHealth')">✅ Health Check</button>
            <button class="sub-tab" onclick="switchSubTab(event, 'appdMonitoring')">▶️ Start Monitoring</button>
        </div>
        
        <!-- ========== SUB-TAB 1: DISCOVERY ========== -->
        <div id="appdDiscovery" class="sub-tab-content active">
            <h3>🔍 AppDynamics Discovery & Configuration</h3>
            <p style="color:#666;margin-bottom:20px;">
                Discover AppDynamics applications and save configuration for the selected LOB and Track.
            </p>
            
            <div class="form-grid">
                <div class="form-group">
                    <label for="discoveryLob">LOB Name <span class="required">*</span></label>
                    <select id="discoveryLob" onchange="onDiscoveryLobChange()">
                        <option value="">-- Select LOB --</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="discoveryTrack">Track</label>
                    <select id="discoveryTrack">
                        <option value="">-- Select Track --</option>
                    </select>
                </div>
            </div>
            
            <button class="btn btn-primary" onclick="runDiscovery()">🔄 Run Discovery & Save Config</button>
            
            <div id="discoveryResults" style="margin-top:20px;"></div>
        </div>
        
        <!-- ========== SUB-TAB 2: HEALTH CHECK ========== -->
        <div id="appdHealth" class="sub-tab-content">
            <h3>✅ Health Check - Database Connectivity Status</h3>
            <p style="color:#666;margin-bottom:20px;">
                Check Oracle databases health and AppDynamics connectivity for LOB/Track.
            </p>
            
            <div class="form-grid">
                <div class="form-group">
                    <label for="healthLob">LOB Name <span class="required">*</span></label>
                    <select id="healthLob" onchange="onHealthLobChange()">
                        <option value="">-- Select LOB --</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="healthTrack">Track</label>
                    <select id="healthTrack">
                        <option value="">-- Select Track --</option>
                    </select>
                </div>
            </div>
            
            <button class="btn btn-refresh" onclick="checkHealth()">🔄 Refresh Health Status</button>
            
            <div id="healthResults" style="margin-top:20px;"></div>
        </div>
        
        <!-- ========== SUB-TAB 3: START MONITORING ========== -->
        <div id="appdMonitoring" class="sub-tab-content">
            <h3>▶️ Start Monitoring Session</h3>
            <p style="color:#666;margin-bottom:20px;">
                Start AppDynamics monitoring session. Data will be collected at 5-minute intervals.
            </p>
            
            <div class="form-grid">
                <div class="form-group">
                    <label for="monitorLob">LOB Name <span class="required">*</span></label>
                    <select id="monitorLob" onchange="onMonitorLobChange()">
                        <option value="">-- Select LOB --</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="monitorTrack">Track <span class="required">*</span></label>
                    <select id="monitorTrack">
                        <option value="">-- Select Track --</option>
                    </select>
                    <small>Track is required for monitoring</small>
                </div>
                
                <div class="form-group">
                    <label for="monitorDuration">Monitoring Duration</label>
                    <select id="monitorDuration">
                        <option value="300">5 minutes</option>
                        <option value="600">10 minutes</option>
                        <option value="1200">20 minutes</option>
                        <option value="2400">40 minutes</option>
                        <option value="7200">2 hours</option>
                        <option value="">Run until manually stopped</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="monitorPcRunId">PC Run ID (for correlation)</label>
                    <input type="text" id="monitorPcRunId" placeholder="Optional 5-digit run ID" maxlength="5">
                    <small>Link monitoring data to Performance Center test</small>
                </div>
            </div>
            
            <button class="btn btn-primary" onclick="startMonitoring()">▶️ Start Monitoring</button>
            <button class="btn btn-secondary" onclick="refreshSessions()">🔄 Refresh Sessions</button>
            
            <div id="monitoringStatus" style="margin-top:20px;"></div>
            
            <!-- Active Sessions -->
            <div class="active-sessions-section" style="margin-top:30px;">
                <h4>📊 Active Monitoring Sessions</h4>
                <p style="color:#666;font-size:13px;">Below are currently active monitoring sessions</p>
                <div id="activeSessions">
                    <p>No active sessions. Start monitoring to see sessions here.</p>
                </div>
            </div>
        </div>
    `;
}

function init_appdynamics() {
    // Populate all LOB dropdowns
    ['discoveryLob', 'healthLob', 'monitorLob'].forEach(id => {
        const select = document.getElementById(id);
        Object.keys(CONFIG.LOB_MONITORING_MAP).forEach(lob => {
            const option = document.createElement('option');
            option.value = lob;
            option.textContent = lob;
            select.appendChild(option);
        });
        if (STATE.currentLOB) {
            select.value = STATE.currentLOB;
        }
    });
    
    // Initialize tracks
    if (STATE.currentLOB) {
        onDiscoveryLobChange();
        onHealthLobChange();
        onMonitorLobChange();
    }
    
    // Load active sessions
    refreshSessions();
}

function onDiscoveryLobChange() {
    updateTracks('discoveryLob', 'discoveryTrack');
}

function onHealthLobChange() {
    updateTracks('healthLob', 'healthTrack');
}

function onMonitorLobChange() {
    updateTracks('monitorLob', 'monitorTrack');
}

async function runDiscovery() {
    const lob = document.getElementById('discoveryLob').value;
    const track = document.getElementById('discoveryTrack').value;
    
    if (!lob) {
        showError('discoveryResults', '⚠ Please select LOB');
        return;
    }
    
    showLoading('discoveryResults', 'Running AppDynamics discovery...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/appd/discovery/run`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                lob_name: lob,
                track: track || null
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const appsCount = data.applications_count || 0;
            const nodesCount = data.nodes_count || 0;
            
            const successHTML = `
                <div class="alert alert-success">
                    <strong>✓ Discovery completed successfully!</strong><br>
                    <strong>Applications discovered:</strong> ${appsCount}<br>
                    <strong>Nodes discovered:</strong> ${nodesCount}<br>
                    <strong>Configuration saved for:</strong> ${lob}${track ? ' | Track: ' + track : ''}<br>
                    <small>You can now proceed to start monitoring with this configuration</small>
                </div>
            `;
            document.getElementById('discoveryResults').innerHTML = successHTML;
            
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
        showError('healthResults', '⚠ Please select LOB');
        return;
    }
    
    showLoading('healthResults', 'Checking database connectivity and AppD health...');
    
    try {
        const response = await Auth.authenticatedFetch(
            `${CONFIG.API_BASE}/monitoring/appd/health?lob_name=${encodeURIComponent(lob)}${track ? '&track=' + encodeURIComponent(track) : ''}`
        );
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const databases = data.databases || [];
            
            let html = '<h4>Database Connectivity Status:</h4>';
            
            if (databases.length === 0) {
                html += '<p style="color:#999;">No databases found for this LOB/Track</p>';
            } else {
                html += '<div class="stat-grid">';
                databases.forEach(db => {
                    const statusColor = db.status === 'Connected' ? '#4caf50' : '#f44336';
                    html += `
                        <div class="stat-card" style="border-left:4px solid ${statusColor};">
                            <h4>${db.database_name}</h4>
                            <div class="value" style="color:${statusColor};">${db.status}</div>
                            ${db.error ? `<small style="color:#f44336;">Error: ${db.error}</small>` : ''}
                        </div>
                    `;
                });
                html += '</div>';
            }
            
            // AppD Status
            html += `
                <div class="alert alert-info" style="margin-top:20px;">
                    <strong>AppDynamics Status:</strong> ${data.appd_status || 'Operational'}<br>
                    <strong>LOB:</strong> ${lob}${track ? ' | Track: ' + track : ''}
                </div>
            `;
            
            document.getElementById('healthResults').innerHTML = html;
            
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
        showError('monitoringStatus', '⚠ Please select LOB');
        return;
    }
    
    if (!track) {
        showError('monitoringStatus', '⚠ Please select Track (required for monitoring)');
        return;
    }
    
    if (pcRunId && !validatePCRunId(pcRunId)) {
        showError('monitoringStatus', '⚠ PC Run ID must be 5 digits if provided');
        return;
    }
    
    showLoading('monitoringStatus', 'Starting AppDynamics monitoring session...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/appd/monitoring/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                lob_name: lob,
                track: track,
                duration_seconds: duration ? parseInt(duration) : null,
                pc_run_id: pcRunId || null
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const successHTML = `
                <div class="alert alert-success">
                    <strong>✓ Monitoring session started successfully!</strong><br>
                    <strong>Session ID:</strong> ${data.session_id}<br>
                    <strong>LOB:</strong> ${lob} | <strong>Track:</strong> ${track}<br>
                    ${duration ? `<strong>Duration:</strong> ${parseInt(duration)/60} minutes<br>` : '<strong>Duration:</strong> Until manually stopped<br>'}
                    ${pcRunId ? `<strong>Linked to PC Run ID:</strong> ${pcRunId}<br>` : ''}
                    <small>Metrics will be collected every 5 minutes</small>
                </div>
            `;
            document.getElementById('monitoringStatus').innerHTML = successHTML;
            
            // Clear PC Run ID field
            document.getElementById('monitorPcRunId').value = '';
            
            // Refresh active sessions
            setTimeout(() => refreshSessions(), 1000);
            
        } else {
            showError('monitoringStatus', data.detail || 'Failed to start monitoring');
        }
    } catch (error) {
        showError('monitoringStatus', error.message);
    }
}

async function refreshSessions() {
    try {
        const response = await Auth.authenticatedFetch(
            `${CONFIG.API_BASE}/monitoring/appd/sessions/active?lob_name=${STATE.currentLOB || ''}`
        );
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const sessions = data.sessions || [];
            
            if (sessions.length === 0) {
                document.getElementById('activeSessions').innerHTML = 
                    '<p style="color:#999;text-align:center;padding:20px;">No active monitoring sessions</p>';
                return;
            }
            
            let html = '';
            sessions.forEach(session => {
                const statusColor = session.status === 'RUNNING' ? '#4caf50' : 
                                  session.status === 'COMPLETED' ? '#2196f3' : '#ff9800';
                
                html += `
                    <div class="session-item" style="border-left:4px solid ${statusColor};">
                        <div><strong>Session ID:</strong> ${session.session_id}</div>
                        <div><strong>LOB:</strong> ${session.lob_name} | <strong>Track:</strong> ${session.track}</div>
                        <div><strong>Started:</strong> ${formatDateTime(session.session_start)}</div>
                        ${session.pc_run_id ? `<div><strong>PC Run ID:</strong> ${session.pc_run_id}</div>` : ''}
                        <span style="float:right;padding:4px 8px;background:${statusColor};color:white;border-radius:4px;font-size:11px;">
                            ${session.status}
                        </span>
                    </div>
                `;
            });
            
            document.getElementById('activeSessions').innerHTML = html;
        }
    } catch (error) {
        console.error('Failed to load active sessions:', error);
    }
}
