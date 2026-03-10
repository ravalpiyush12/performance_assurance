// ==========================================
// MONGODB TAB
// ==========================================

function getMongoDBHTML() {
    return `
        <h2>🍃 MongoDB Monitoring</h2>
        
        <div class="form-grid">
            <div class="form-group">
                <label>Collection Name</label>
                <input type="text" id="mongoCollection" placeholder="e.g., performance_metrics">
            </div>
            
            <div class="form-group">
                <label>Query (JSON)</label>
                <textarea id="mongoQuery" rows="4" placeholder='{"field": "value"}'></textarea>
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="executeMongoQuery()">▶️ Execute Query</button>
        
        <div id="mongoResults" style="margin-top: 20px;"></div>
    `;
}

function init_mongodb() {
    // Initialize if needed
}

async function executeMongoQuery() {
    const collection = document.getElementById('mongoCollection').value.trim();
    const query = document.getElementById('mongoQuery').value.trim();
    
    if (!collection) {
        showError('mongoResults', 'Please enter collection name');
        return;
    }
    
    showLoading('mongoResults', 'Executing query...');
    
    try {
        const response = await Auth.authenticatedFetch(`${CONFIG.API_BASE}/monitoring/mongodb/query`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                collection: collection,
                query: query ? JSON.parse(query) : {}
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            const results = data.results || [];
            showSuccess('mongoResults', `✓ Query executed successfully! Found ${results.length} documents`);
        } else {
            showError('mongoResults', data.detail || 'Query failed');
        }
    } catch (error) {
        showError('mongoResults', error.message);
    }
}
