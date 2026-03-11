// ==========================================
// NAVIGATION FUNCTIONS
// ==========================================

function switchMainTab(event, tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from all tab buttons
    document.querySelectorAll('.tab-header .tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');
    
    // Initialize tab if needed
    const initFunc = window[`init_${tabName}`];
    if (typeof initFunc === 'function') {
        initFunc();
    }
}

function switchSubTab(event, subTabName) {
    const parentTab = event.currentTarget.closest('.tab-content');
    
    // Hide all sub-tab contents in this parent
    parentTab.querySelectorAll('.sub-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from all sub-tab buttons
    parentTab.querySelectorAll('.sub-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected sub-tab
    document.getElementById(subTabName).classList.add('active');
    event.currentTarget.classList.add('active');
}

function backToLOBSelector() {
    window.location.href = 'page1-lob-selector.html';
}

function backToHealthDashboard() {
    window.location.href = 'page2-health-dashboard.html';
}
