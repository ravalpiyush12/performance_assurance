// DUMMY DATA
const TOOLS_STATUS = {
    'Digital Technology': [
        { name: 'AppDynamics', icon: '📊', status: 'healthy', nodes: '7/7', uptime: '99.9%' },
        { name: 'Oracle Databases', icon: '🗄️', status: 'healthy', connected: '5/7', uptime: '99.8%' },
        { name: 'Kibana', icon: '📈', status: 'healthy', url: 'Active', uptime: '100%' },
        { name: 'Splunk', icon: '🔍', status: 'healthy', url: 'Active', uptime: '99.9%' },
        { name: 'MongoDB', icon: '🍃', status: 'healthy', nodes: '3/3', uptime: '100%' },
        { name: 'Performance Center', icon: '⚡', status: 'healthy', url: 'Active', uptime: '99.7%' }
    ],
    'Payments': [
        { name: 'AppDynamics', icon: '📊', status: 'healthy', nodes: '2/2', uptime: '99.9%' },
        { name: 'Kibana', icon: '📈', status: 'healthy', url: 'Active', uptime: '100%' }
    ]
};

const TRACKS = {
    'Digital Technology': ['CDV3', 'Track1', 'Track2'],
    'Payments': ['PayTrack1', 'PayTrack2'],
    'Corporate': ['CorpTrack1'],
    'Retail Banking': ['RetailTrack1']
};

// Dummy AppD configs by track (simulating DB fetch)
const APPD_CONFIGS = {
    'CDV3': {
        name: 'NFT_Digital_Technology_CDV3_12Mar2026_2342',
        apps: ['icg-tts-cirp-ng-173720_PTE', 'CDV3_NFT_Digital_Technology', 'CIRP_Digital_Tech']
    },
    'Track1': {
        name: 'Digital_Tech_Track1_10Mar2026_1534',
        apps: ['ServiceTech_API', 'Digital_Platform_Core']
    },
    'PayTrack1': {
        name: 'Payments_Track1_09Mar2026_0845',
        apps: ['Payment_Gateway_API', 'Transaction_Processor']
    }
};

let selectedLOB = null;
let configData = {};

// TOGGLE STEP COLLAPSE
function toggleStep(header) {
    const container = header.parentElement;
    container.classList.toggle('expanded');
}

// EXPAND STEP
function expandStep(stepId) {
    const step = document.getElementById(stepId);
    if (step) {
        step.classList.add('expanded');
        step.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// UPDATE PROGRESS BAR
function updateProgress(stepNum) {
    for (let i = 1; i <= 5; i++) {
        const prog = document.getElementById(`prog${i}`);
        prog.classList.remove('active', 'completed');
        if (i < stepNum) prog.classList.add('completed');
        else if (i === stepNum) prog.classList.add('active');
    }
}

// STEP 1: LOB SELECTED
function onLOBSelected() {
    selectedLOB = document.getElementById('lobSelector').value;
    if (selectedLOB) {
        expandStep('step2');
        updateProgress(2);
    }
}

// STEP 2: VALIDATE
function validatePrerequisites() {
    const statusGrid = document.getElementById('statusGrid');
    const tools = TOOLS_STATUS[selectedLOB] || [];
    
    let html = '';
    tools.forEach(tool => {
        html += `
            <div class="status-card ${tool.status}">
                <div class="status-card-header">
                    <span class="status-card-icon">${tool.icon}</span>
                    <span class="status-badge ${tool.status}">${tool.status === 'healthy' ? 'Operational' : 'Down'}</span>
                </div>
                <div class="status-card-title">${tool.name}</div>
                <div class="status-card-desc">Real-time health monitoring</div>
                ${Object.keys(tool).filter(k => !['name','icon','status'].includes(k)).map(key => `
                    <div class="status-metric">
                        <span class="status-metric-label">${key}:</span>
                        <span class="status-metric-value">${tool[key]}</span>
                    </div>
                `).join('')}
            </div>
        `;
    });
    
    statusGrid.innerHTML = html;
    document.getElementById('validationResults').classList.remove('hidden');
    
    // Populate track dropdown
    const trackSelect = document.getElementById('track');
    trackSelect.innerHTML = '<option value="">-- Select Track --</option>';
    (TRACKS[selectedLOB] || []).forEach(track => {
        trackSelect.innerHTML += `<option value="${track}">${track}</option>`;
    });
    
    setTimeout(() => {
        expandStep('step3');
        updateProgress(3);
    }, 1000);
}

// STEP 3: TRACK SELECTED - AUTO FETCH APPD CONFIG
function onTrackSelected() {
    const track = document.getElementById('track').value;
    if (!track) {
        document.getElementById('appdConfigBox').classList.add('hidden');
        return;
    }

    // Simulate API call to fetch latest AppD config for this track
    const config = APPD_CONFIGS[track] || { name: 'No config found', apps: [] };
    
    document.getElementById('configName').textContent = config.name;
    
    let appsHTML = '';
    config.apps.forEach(app => {
        appsHTML += `<div class="readonly-app">${app}</div>`;
    });
    document.getElementById('appdApps').innerHTML = appsHTML || '<p style="color:#9ca3af;">No applications configured</p>';
    
    document.getElementById('appdConfigBox').classList.remove('hidden');
    
    configData.appdConfig = config.name;
    configData.appdApps = config.apps;
    updateReview();
}

// SWITCH TABS
function switchTab(tabName) {
    document.querySelectorAll('.config-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    if (tabName === 'review') updateReview();
}

// UPDATE REVIEW SUMMARY
function updateReview() {
    configData.pcRunId = document.getElementById('pcRunId').value;
    configData.track = document.getElementById('track').value;
    configData.duration = document.getElementById('duration').value;
    configData.testName = document.getElementById('testName').value;
    configData.kibanaDashboard = document.getElementById('kibanaDashboard').value;
    configData.splunkDashboard = document.getElementById('splunkDashboard').value;
    configData.mongoCollections = document.getElementById('mongoCollections').value;

    const durationText = configData.duration ? `${configData.duration / 60} minutes` : 'Until manually stopped';

    const html = `
        <div style="display:grid;grid-template-columns:200px 1fr;gap:15px;font-size:14px;">
            <div style="font-weight:700;color:#6b7280;">PC Run ID:</div>
            <div style="font-weight:800;color:#111827;">${configData.pcRunId || '(Not set)'}</div>
            
            <div style="font-weight:700;color:#6b7280;">Track:</div>
            <div style="font-weight:800;color:#111827;">${configData.track || '(Not set)'}</div>
            
            <div style="font-weight:700;color:#6b7280;">Duration:</div>
            <div>${durationText}</div>
            
            <div style="font-weight:700;color:#6b7280;">Test Name:</div>
            <div>${configData.testName || '(Not set)'}</div>
            
            <div style="font-weight:700;color:#6b7280;">AppD Config:</div>
            <div style="font-weight:600;color:#1e40af;">${configData.appdConfig || '(Not loaded)'}</div>
            
            <div style="font-weight:700;color:#6b7280;">AppD Apps:</div>
            <div>${(configData.appdApps || []).join(', ') || '(None)'}</div>
            
            <div style="font-weight:700;color:#6b7280;">Kibana Dashboard:</div>
            <div>${configData.kibanaDashboard || '(Not set)'}</div>
            
            <div style="font-weight:700;color:#6b7280;">Splunk Dashboard:</div>
            <div>${configData.splunkDashboard || '(Not set)'}</div>
            
            <div style="font-weight:700;color:#6b7280;">MongoDB Collections:</div>
            <div>${configData.mongoCollections || '(Not set)'}</div>
        </div>
    `;

    document.getElementById('reviewSummary').innerHTML = html;
}

// START MONITORING
function startMonitoring() {
    if (!configData.pcRunId || configData.pcRunId.length !== 5) {
        alert('⚠ Please enter valid 5-digit PC Run ID');
        switchTab('basic');
        return;
    }
    if (!configData.track) {
        alert('⚠ Please select Track');
        switchTab('basic');
        return;
    }

    const tools = TOOLS_STATUS[selectedLOB] || [];
    const progressItems = document.getElementById('progressItems');
    
    let html = '';
    tools.forEach((tool, index) => {
        html += `
            <div class="progress-item">
                <div class="progress-header">
                    <span class="progress-label">${tool.icon} ${tool.name}</span>
                    <span class="progress-status" id="status${index}">Initializing...</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" id="progress${index}" style="width: 0%"></div>
                </div>
            </div>
        `;
    });
    
    progressItems.innerHTML = html;
    document.getElementById('monitoringProgress').classList.remove('hidden');
    document.getElementById('startBtn').disabled = true;
    
    tools.forEach((tool, index) => {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                document.getElementById(`status${index}`).textContent = '✓ Active';
                document.getElementById(`progress${index}`).classList.add('complete');
            }
            document.getElementById(`progress${index}`).style.width = progress + '%';
            document.getElementById(`status${index}`).textContent = Math.floor(progress) + '%';
        }, 500);
    });
    
    setTimeout(() => {
        expandStep('step4');
        updateProgress(4);
    }, 3000);
}

// STOP MONITORING
function stopMonitoring() {
    document.getElementById('stopBtn').disabled = true;
    
    const tables = [
        { name: 'MASTER_TEST_RUN', records: 1 },
        { name: 'APPD_MONITORING_DATA', records: 145 },
        { name: 'APPD_TRANSACTION_STATS', records: 523 },
        { name: 'ORACLE_AWR_SNAPSHOTS', records: 12 },
        { name: 'KIBANA_LOG_ENTRIES', records: 8934 },
        { name: 'SPLUNK_EVENT_DATA', records: 6721 },
        { name: 'MONGODB_METRICS', records: 234 },
        { name: 'PC_RUN_SUMMARY', records: 1 }
    ];

    let html = `
        <div style="margin-bottom:15px;"><strong>Primary Key:</strong> PC Run ID = ${configData.pcRunId}</div>
        <table style="width:100%;border-collapse:collapse;">
            <thead>
                <tr style="background:#e5e7eb;">
                    <th style="padding:12px;text-align:left;border:1px solid #d1d5db;font-weight:800;">Table Name</th>
                    <th style="padding:12px;text-align:right;border:1px solid #d1d5db;font-weight:800;">Records Inserted</th>
                </tr>
            </thead>
            <tbody>
    `;

    tables.forEach(table => {
        html += `
            <tr>
                <td style="padding:10px;border:1px solid #d1d5db;font-weight:600;">${table.name}</td>
                <td style="padding:10px;text-align:right;border:1px solid #d1d5db;font-weight:700;">${table.records.toLocaleString()}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
            <tfoot>
                <tr style="background:#f3f4f6;">
                    <td style="padding:12px;border:1px solid #d1d5db;font-weight:800;">TOTAL</td>
                    <td style="padding:12px;text-align:right;border:1px solid #d1d5db;font-weight:800;">${tables.reduce((sum, t) => sum + t.records, 0).toLocaleString()}</td>
                </tr>
            </tfoot>
        </table>
    `;

    document.getElementById('tablesSummary').innerHTML = html;
    document.getElementById('stopResults').classList.remove('hidden');
    
    setTimeout(() => {
        expandStep('step5');
        updateProgress(5);
    }, 1000);
}

// UPLOAD HANDLERS
function handleAWRUpload(input) {
    if (input.files.length > 0) {
        document.getElementById('awrFileName').textContent = '✓ ' + input.files[0].name;
        checkProcessButton();
    }
}

function handlePCUpload(input) {
    if (input.files.length > 0) {
        document.getElementById('pcFileName').textContent = '✓ ' + input.files[0].name;
        checkProcessButton();
    }
}

function checkProcessButton() {
    const awrFile = document.getElementById('awrFile').files.length > 0;
    const pcFile = document.getElementById('pcFile').files.length > 0;
    document.getElementById('processBtn').disabled = !(awrFile && pcFile);
}

function processReports() {
    document.getElementById('processBtn').disabled = true;
    
    const processingHTML = `
        <div class="alert alert-success">
            <strong>✓ Reports Processed Successfully!</strong>
        </div>
        <div style="background:#f9fafb;padding:20px;border-radius:12px;">
            <h4 style="margin-bottom:15px;">📊 Processing Summary</h4>
            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="padding:10px;border:1px solid #d1d5db;font-weight:700;">AWR Report</td>
                    <td style="padding:10px;border:1px solid #d1d5db;">Parsed and inserted into <strong>ORACLE_AWR_METRICS</strong> (847 metrics)</td>
                </tr>
                <tr>
                    <td style="padding:10px;border:1px solid #d1d5db;font-weight:700;">PC Report</td>
                    <td style="padding:10px;border:1px solid #d1d5db;">Extracted and stored in <strong>PC_TRANSACTION_DETAILS</strong> (234 transactions)</td>
                </tr>
                <tr style="background:#ecfdf5;">
                    <td style="padding:10px;border:1px solid #d1d5db;font-weight:700;">Status</td>
                    <td style="padding:10px;border:1px solid #d1d5db;color:#065f46;font-weight:700;">✓ All data successfully stored in Oracle DB</td>
                </tr>
            </table>
        </div>
    `;

    document.getElementById('processingResults').innerHTML = processingHTML;
    document.getElementById('processingResults').classList.remove('hidden');
}
