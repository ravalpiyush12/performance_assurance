// ==========================================
// GLOBAL CONFIGURATION
// ==========================================

const CONFIG = {
    // API Configuration
    API_BASE: 'http://localhost:8000/api/v1',
    
    // LOB to Monitoring Tools Mapping
    LOB_MONITORING_MAP: {
        'Digital Technology': ['APPD', 'AWR', 'KIBANA', 'SPLUNK', 'MONGODB', 'PC'],
        'Payments': ['APPD', 'KIBANA'],
        'Corporate': ['APPD', 'AWR'],
        'Retail Banking': ['APPD', 'KIBANA', 'SPLUNK']
    },
    
    // Monitoring Tools Metadata
    MONITORING_TOOLS: {
        'APPD': { name: 'AppDynamics', icon: '📊' },
        'AWR': { name: 'AWR Analysis', icon: '📉' },
        'KIBANA': { name: 'Kibana', icon: '📈' },
        'SPLUNK': { name: 'Splunk', icon: '🔍' },
        'MONGODB': { name: 'MongoDB', icon: '🍃' },
        'PC': { name: 'Performance Center', icon: '⚡' }
    },
    
    // Track Options per LOB
    TRACKS: {
        'Digital Technology': ['Track1', 'Track2', 'Track3'],
        'Payments': ['PayTrack1', 'PayTrack2'],
        'Corporate': ['CorpTrack1'],
        'Retail Banking': ['RetailTrack1', 'RetailTrack2']
    },
    
    // Database Options
    DATABASES: ['PRODDB', 'TESTDB', 'DEVDB', 'ORCL'],
    
    // Session Settings
    SESSION_EXPIRY_MINUTES: 60,
    POLL_INTERVAL: 30000
};

// Global State
const STATE = {
    currentLOB: null,
    sessionToken: null,
    currentUser: null,
    currentTestRun: null
};
