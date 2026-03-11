// ==========================================
// SPLUNK ANALYSIS TAB - Complete Implementation
// Based on original index.html working code
// ==========================================

function getSplunkHTML() {
    return `
        <h2>🔍 Splunk Log Analysis</h2>
        <p style="color:#666;margin-bottom:20px;">
            Search and analyze logs using Splunk query language.
        </p>
        
        <div class="form-grid">
            <div class="form-group">
                <label for="splunkQuery">Search Query (SPL)</label>
                <textarea id="splunkQuery" rows="4" placeholder='Enter Splunk query (e.g., index=main sourcetype=api status=error | stats count by host)'></textarea>
                <small>Use Splunk Processing Language (SPL) syntax</small>
            </div>
            
            <div class="form-group">
                <label for="splunkTimeRange">Time Range</label>
                <select id="splunkTimeRange">
                    <option value="15m">Last 15 minutes</option>
                    <option value="30m">Last 30 minutes</option>
                    <option value="1h">Last 1 hour</option>
                    <option value="6h">Last 6 hours</option>
                    <option value="24h">Last 24 hours</option>
                    <option value="7d">Last 7 days</option>
                </select>
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="executeSplunkQuery()">▶️ Execute Search</button>
        
        <div id="splunkResults" style="margin-top:20px;"></div>
    `;
}

function init_splunk() {
    // Initialize if needed
}

async function executeSplunkQuery() {
    const query = document.getElementById('splunkQuery').value.trim();
    const timeRange = document.getElementById('splunkTimeRange').value;
    
    if (!query) {
        showError('splunkResults', '⚠ Please enter a search query');
        return;
    }
    
    showLoading('splunkResults', 'Executing Splunk query...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/splunk/search`, {
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
            const totalCount = data.result_count || results.length;
            
            let html = `
                <div class="alert alert-success">
                    <strong>✓ Splunk query executed successfully!</strong><br>
                    <strong>Result Count:</strong> ${totalCount}<br>
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
            
            document.getElementById('splunkResults').innerHTML = html;
            
        } else {
            showError('splunkResults', data.detail || 'Query execution failed');
        }
    } catch (error) {
        showError('splunkResults', error.message);
    }
}
