// API Configuration
const API_CONFIG = {
    // API Gateway endpoint (will be set after deployment)
    apiEndpoint: window.API_ENDPOINT || 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod',
    
    // AWS Cognito configuration (will be set after deployment)
    cognito: {
        userPoolId: window.COGNITO_USER_POOL_ID || 'us-east-1_XXXXXXXXX',
        clientId: window.COGNITO_CLIENT_ID || 'XXXXXXXXXXXXXXXXXXXXXXXXXX',
        region: window.COGNITO_REGION || 'us-east-1'
    }
};

// API Endpoints
const API_ENDPOINTS = {
    // Authentication
    signup: '/auth/signup',
    login: '/auth/login',
    logout: '/auth/logout',
    refresh: '/auth/refresh',
    
    // User Management
    getUser: '/users/me',
    updateUser: '/users/me',
    
    // Data Sources
    listSources: '/data-sources',
    addSource: '/data-sources',
    updateSource: (id) => `/data-sources/${id}`,
    deleteSource: (id) => `/data-sources/${id}`,
    testSource: (id) => `/data-sources/${id}/test`,
    
    // Notifications
    getNotifications: '/notifications',
    getStats: '/stats',
    getStatus: '/status',
    
    // Settings
    getSettings: '/settings',
    updateSettings: '/settings'
};

// Helper function to build full API URL
function getApiUrl(endpoint) {
    return `${API_CONFIG.apiEndpoint}${endpoint}`;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API_CONFIG, API_ENDPOINTS, getApiUrl };
}

