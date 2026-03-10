// ==========================================
// KIBANA TAB
// ==========================================

function getKibanaHTML() {
    return `
        <h2>📈 Kibana / Elasticsearch Monitoring</h2>
        
        <div class="form-grid">
            <div class="form-group">
                <label>Search Query</label>
                <textarea id="kibanaQuery" rows="4" placeholder="Enter Elasticsearch query"></textarea>
            </div>
            
            <div class="form-group">
                <label>Time Range</label>
                <select id="kibanaTimeRange">
                    <option value="15m">Last 15 minutes</option>
                    <option value="30m">Last 30 minutes</option>
                    <option value="1h">Last 1 hour</option>
                    <option value="24h">Last 24 hours</option>
                </select>
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="executeKibanaQuery()">▶️ Execute Query</button>
        
        <div id="kibanaResults" style="margin-top: 20px;"></div>
    `;
}

function init_kibana() {
    // Initialize if needed
}

async function executeKibanaQuery() {
    const query = document.getElementById('kibanaQuery').value.trim();
    const timeRange = document.getElementById('kibanaTimeRange').value;
    
    if (!query) {
        showError('kibanaResults', 'Please enter a query');
        return;
    }
    
    showLoading('kibanaResults', 'Executing query...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/kibana/search`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ query: query, time_range: timeRange })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const results = data.results || [];
            showSuccess('kibanaResults', `✓ Query executed successfully! Found ${results.length} results`);
        } else {
            showError('kibanaResults', data.detail || 'Query failed');
        }
    } catch (error) {
        showError('kibanaResults', error.message);
    }
}
