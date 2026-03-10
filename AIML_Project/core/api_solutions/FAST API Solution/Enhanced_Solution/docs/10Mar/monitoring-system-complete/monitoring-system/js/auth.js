// ==========================================
// AUTHENTICATION MODULE
// ==========================================

const Auth = {
    async login(username, password, totpCode) {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/auth/login`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: username,
                    password: password,
                    totp_code: totpCode || null
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                STATE.sessionToken = data.session_token;
                localStorage.setItem('session_token', STATE.sessionToken);
                
                STATE.currentUser = {
                    user_id: data.user_id,
                    username: data.username,
                    email: data.email,
                    full_name: data.full_name,
                    role: data.role
                };
                
                await this.loadPermissions();
                return { success: true, user: STATE.currentUser };
            }
            
            return { success: false, error: data.detail || 'Login failed' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },
    
    async loadPermissions() {
        try {
            const response = await this.authenticatedFetch(`${CONFIG.API_BASE}/auth/me`);
            if (response.ok) {
                const data = await response.json();
                STATE.currentUser.permissions = data.permissions;
            }
        } catch (error) {
            console.error('Error loading permissions:', error);
        }
    },
    
    async logout() {
        if (STATE.sessionToken) {
            try {
                await fetch(`${CONFIG.API_BASE}/auth/logout`, {
                    method: 'POST',
                    headers: {'Authorization': `Bearer ${STATE.sessionToken}`}
                });
            } catch (error) {
                console.error('Logout error:', error);
            }
        }
        
        STATE.sessionToken = null;
        STATE.currentUser = null;
        STATE.currentLOB = null;
        STATE.currentTestRun = null;
        localStorage.removeItem('session_token');
        
        window.location.href = '../pages/page1-lob-selector.html';
    },
    
    async validateSession(token) {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/auth/me`, {
                headers: {'Authorization': `Bearer ${token}`}
            });
            
            if (response.ok) {
                const data = await response.json();
                STATE.currentUser = data;
                STATE.sessionToken = token;
                return true;
            }
            return false;
        } catch (error) {
            return false;
        }
    },
    
    async authenticatedFetch(url, options = {}) {
        if (!STATE.sessionToken) {
            throw new Error('Not authenticated');
        }
        
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${STATE.sessionToken}`;
        
        const response = await fetch(url, options);
        
        if (response.status === 401) {
            this.logout();
            throw new Error('Session expired');
        }
        
        return response;
    },
    
    hasPermission(permission) {
        return STATE.currentUser?.permissions?.includes(permission);
    },
    
    isAdmin() {
        return STATE.currentUser?.role === 'admin';
    }
};

async function checkAuthentication() {
    const token = localStorage.getItem('session_token');
    if (!token) {
        window.location.href = 'page3-login.html';
        return false;
    }
    
    const valid = await Auth.validateSession(token);
    if (!valid) {
        localStorage.removeItem('session_token');
        window.location.href = 'page3-login.html';
        return false;
    }
    
    return true;
}
