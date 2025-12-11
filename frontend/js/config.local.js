// Local Development Configuration
// This file overrides config.js for local development

// Mock API endpoint for local development
const API_CONFIG = {
    // For local development, we'll use a mock API or point to a local server
    apiEndpoint: window.API_ENDPOINT || 'http://localhost:3000',
    
    // Mock Cognito config (not used in local dev)
    cognito: {
        userPoolId: 'local-dev',
        clientId: 'local-dev',
        region: 'us-east-1'
    }
};

// API Endpoints (same as config.js)
const API_ENDPOINTS = {
    signup: '/auth/signup',
    login: '/auth/login',
    logout: '/auth/logout',
    refresh: '/auth/refresh',
    getUser: '/users/me',
    updateUser: '/users/me',
    listSources: '/data-sources',
    addSource: '/data-sources',
    updateSource: (id) => `/data-sources/${id}`,
    deleteSource: (id) => `/data-sources/${id}`,
    testSource: (id) => `/data-sources/${id}/test`,
    getNotifications: '/notifications',
    getStats: '/stats',
    getStatus: '/status',
    getSettings: '/settings',
    updateSettings: '/settings'
};

function getApiUrl(endpoint) {
    return `${API_CONFIG.apiEndpoint}${endpoint}`;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API_CONFIG, API_ENDPOINTS, getApiUrl };
}

