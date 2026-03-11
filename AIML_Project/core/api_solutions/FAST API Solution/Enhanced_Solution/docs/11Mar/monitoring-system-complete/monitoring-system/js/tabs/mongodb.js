// ==========================================
// MONGODB ANALYSIS TAB - Complete Implementation
// Based on original index.html working code
// ==========================================

function getMongoDBHTML() {
    return `
        <h2>🍃 MongoDB Collection Monitoring</h2>
        <p style="color:#666;margin-bottom:20px;">
            Query MongoDB collections for monitoring data analysis.
        </p>
        
        <div class="form-grid">
            <div class="form-group">
                <label for="mongoCollection">Collection Name <span class="required">*</span></label>
                <input type="text" id="mongoCollection" placeholder="e.g., performance_metrics">
                <small>Enter the MongoDB collection name to query</small>
            </div>
            
            <div class="form-group">
                <label for="mongoQuery">Query (JSON)</label>
                <textarea id="mongoQuery" rows="4" placeholder='{"field": "value", "timestamp": {"$gte": "2026-01-01"}}'></textarea>
                <small>MongoDB query in JSON format (leave empty for all documents)</small>
            </div>
            
            <div class="form-group">
                <label for="mongoLimit">Limit Results</label>
                <select id="mongoLimit">
                    <option value="10">10 documents</option>
                    <option value="50">50 documents</option>
                    <option value="100">100 documents</option>
                    <option value="500">500 documents</option>
                </select>
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="executeMongoQuery()">▶️ Execute Query</button>
        
        <div id="mongoResults" style="margin-top:20px;"></div>
    `;
}

function init_mongodb() {
    // Initialize if needed
}

async function executeMongoQuery() {
    const collection = document.getElementById('mongoCollection').value.trim();
    const queryStr = document.getElementById('mongoQuery').value.trim();
    const limit = parseInt(document.getElementById('mongoLimit').value);
    
    if (!collection) {
        showError('mongoResults', '⚠ Please enter collection name');
        return;
    }
    
    // Validate JSON if query is provided
    let query = {};
    if (queryStr) {
        try {
            query = JSON.parse(queryStr);
        } catch (e) {
            showError('mongoResults', '⚠ Invalid JSON query format');
            return;
        }
    }
    
    showLoading('mongoResults', 'Querying MongoDB collection...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/mongodb/query`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                collection: collection,
                query: query,
                limit: limit
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const results = data.results || [];
            const totalCount = data.total_count || results.length;
            
            let html = `
                <div class="alert alert-success">
                    <strong>✓ MongoDB query executed successfully!</strong><br>
                    <strong>Collection:</strong> ${collection}<br>
                    <strong>Total Documents:</strong> ${totalCount}<br>
                    <strong>Documents Returned:</strong> ${results.length}
                </div>
            `;
            
            if (results.length > 0) {
                html += '<div style="margin-top:20px;"><h4>Query Results:</h4>';
                results.forEach((doc, index) => {
                    html += `
                        <div class="test-item">
                            <div><strong>Document ${index + 1}:</strong></div>
                            <pre style="background:#f5f5f5;padding:10px;border-radius:4px;overflow-x:auto;">
${JSON.stringify(doc, null, 2)}
                            </pre>
                        </div>
                    `;
                });
                html += '</div>';
            } else {
                html += '<p style="color:#999;text-align:center;padding:20px;">No documents found matching the query</p>';
            }
            
            document.getElementById('mongoResults').innerHTML = html;
            
        } else {
            showError('mongoResults', data.detail || 'Query execution failed');
        }
    } catch (error) {
        showError('mongoResults', error.message);
    }
}
