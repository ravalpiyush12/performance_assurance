// ==========================================
// UTILITY FUNCTIONS
// ==========================================

function formatDateTime(date) {
    if (!date) return '--';
    return new Date(date).toLocaleString();
}

function formatNumber(num) {
    if (num == null) return '--';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function showLoading(elementId, message = 'Loading...') {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = `<div class="loading">${message}</div>`;
}

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = `<div class="alert alert-error">${message}</div>`;
}

function showSuccess(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = `<div class="alert alert-success">${message}</div>`;
}

function populateDropdown(elementId, options, placeholder = '-- Select --') {
    const select = document.getElementById(elementId);
    if (!select) return;
    
    select.innerHTML = `<option value="">${placeholder}</option>`;
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = typeof opt === 'string' ? opt : opt.value;
        option.textContent = typeof opt === 'string' ? opt : opt.label;
        select.appendChild(option);
    });
}

function validatePCRunId(runId) {
    return /^\d{5}$/.test(runId);
}

function escapeHtml(text) {
    const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
    return text.replace(/[&<>"']/g, m => map[m]);
}

function startSessionTimer() {
    let remainingMinutes = CONFIG.SESSION_EXPIRY_MINUTES;
    
    const timer = setInterval(() => {
        remainingMinutes--;
        const hours = Math.floor(remainingMinutes / 60);
        const mins = remainingMinutes % 60;
        const display = hours > 0 ? `⏱ ${hours}h ${mins}m left` : `⏱ ${mins} min left`;
        
        const timerEl = document.getElementById('sessionTimer');
        if (timerEl) {
            timerEl.textContent = display;
            if (remainingMinutes === 5) {
                timerEl.style.color = '#ff9800';
                alert('⚠️ Your session will expire in 5 minutes');
            }
            if (remainingMinutes <= 0) {
                clearInterval(timer);
                alert('❌ Session expired');
                Auth.logout();
            }
        }
    }, 60000);
}
