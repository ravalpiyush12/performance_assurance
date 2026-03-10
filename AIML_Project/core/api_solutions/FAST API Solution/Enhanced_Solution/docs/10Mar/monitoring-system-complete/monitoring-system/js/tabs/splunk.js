// ==========================================
// SPLUNK TAB
// ==========================================

function getSplunkHTML() {
    return `
        <h2>🔍 Splunk Monitoring</h2>
        
        <div class="form-grid">
            <div class="form-group">
                <label>Search Query</label>
                <textarea id="splunkQuery" rows="4" placeholder="Enter Splunk search query"></textarea>
            </div>
            
            <div class="form-group">
                <label>Time Range</label>
                <select id="splunkTimeRange">
                    <option value="15m">Last 15 minutes</option>
                    <option value="30m">Last 30 minutes</option>
                    <option value="1h">Last 1 hour</option>
                    <option value="24h">Last 24 hours</option>
                </select>
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="executeSplunkQuery()">▶️ Execute Query</button>
        
        <div id="splunkResults" style="margin-top: 20px;"></div>
    `;
}

function init_splunk() {
    // Initialize if needed
}

async function executeSplunkQuery() {
    const query = document.getElementById('splunkQuery').value.trim();
    const timeRange = document.getElementById('splunkTimeRange').value;
    
    if (!query) {
        showError('splunkResults', 'Please enter a query');
        return;
    }
    
    showLoading('splunkResults', 'Executing query...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/splunk/search`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ query: query, time_range: timeRange })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const results = data.results || [];
            showSuccess('splunkResults', `✓ Query executed successfully! Found ${results.length} results`);
        } else {
            showError('splunkResults', data.detail || 'Query failed');
        }
    } catch (error) {
        showError('splunkResults', error.message);
    }
}
