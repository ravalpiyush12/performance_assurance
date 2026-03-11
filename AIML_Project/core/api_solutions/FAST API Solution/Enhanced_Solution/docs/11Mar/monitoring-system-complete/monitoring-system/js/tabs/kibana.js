// ==========================================
// KIBANA ANALYSIS TAB - Complete Implementation
// Based on original index.html working code
// ==========================================

function getKibanaHTML() {
    return `
        <h2>📈 Kibana / Elasticsearch Monitoring</h2>
        <p style="color:#666;margin-bottom:20px;">
            Search and analyze Elasticsearch logs through Kibana interface.
        </p>
        
        <div class="form-grid">
            <div class="form-group">
                <label for="kibanaQuery">Search Query</label>
                <textarea id="kibanaQuery" rows="4" placeholder='Enter Elasticsearch query (e.g., status:error AND service:api)'></textarea>
                <small>Use Elasticsearch query syntax</small>
            </div>
            
            <div class="form-group">
                <label for="kibanaTimeRange">Time Range</label>
                <select id="kibanaTimeRange">
                    <option value="15m">Last 15 minutes</option>
                    <option value="30m">Last 30 minutes</option>
                    <option value="1h">Last 1 hour</option>
                    <option value="6h">Last 6 hours</option>
                    <option value="24h">Last 24 hours</option>
                    <option value="7d">Last 7 days</option>
                </select>
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="executeKibanaQuery()">▶️ Execute Search</button>
        
        <div id="kibanaResults" style="margin-top:20px;"></div>
    `;
}

function init_kibana() {
    // Initialize if needed
}

async function executeKibanaQuery() {
    const query = document.getElementById('kibanaQuery').value.trim();
    const timeRange = document.getElementById('kibanaTimeRange').value;
    
    if (!query) {
        showError('kibanaResults', '⚠ Please enter a search query');
        return;
    }
    
    showLoading('kibanaResults', 'Executing Elasticsearch query...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/kibana/search`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: query,
                time_range: timeRange
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const results = data.results || [];
            const totalHits = data.total_hits || results.length;
            
            let html = `
                <div class="alert alert-success">
                    <strong>✓ Query executed successfully!</strong><br>
                    <strong>Total Hits:</strong> ${totalHits}<br>
                    <strong>Time Range:</strong> ${timeRange}<br>
                    <strong>Results Returned:</strong> ${results.length}
                </div>
            `;
            
            if (results.length > 0) {
                html += '<div style="margin-top:20px;"><h4>Search Results:</h4>';
                results.slice(0, 10).forEach((result, index) => {
                    html += `
                        <div class="test-item">
                            <div><strong>Result ${index + 1}:</strong></div>
                            <pre style="background:#f5f5f5;padding:10px;border-radius:4px;overflow-x:auto;">
${JSON.stringify(result, null, 2)}
                            </pre>
                        </div>
                    `;
                });
                
                if (results.length > 10) {
                    html += `<p style="color:#666;text-align:center;">Showing first 10 of ${results.length} results</p>`;
                }
                
                html += '</div>';
            }
            
            document.getElementById('kibanaResults').innerHTML = html;
            
        } else {
            showError('kibanaResults', data.detail || 'Query execution failed');
        }
    } catch (error) {
        showError('kibanaResults', error.message);
    }
}
