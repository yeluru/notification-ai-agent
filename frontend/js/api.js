// API Client for making authenticated requests
class ApiClient {
    constructor() {
        this.baseUrl = API_CONFIG.apiEndpoint;
    }

    async request(endpoint, options = {}) {
        const url = getApiUrl(endpoint);
        const headers = {
            ...authManager.getAuthHeaders(),
            ...options.headers
        };

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);
            
            // Handle token refresh on 401
            if (response.status === 401) {
                const refreshed = await authManager.refreshToken();
                if (refreshed) {
                    // Retry request with new token
                    headers['Authorization'] = `Bearer ${authManager.token}`;
                    const retryResponse = await fetch(url, { ...config, headers });
                    return this.handleResponse(retryResponse);
                } else {
                    // Refresh failed, logout user
                    authManager.logout();
                    throw new Error('Session expired. Please login again.');
                }
            }

            return this.handleResponse(response);
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }

    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } else {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.text();
        }
    }

    // User Management
    async getUser() {
        return this.request(API_ENDPOINTS.getUser, { method: 'GET' });
    }

    async updateUser(userData) {
        return this.request(API_ENDPOINTS.updateUser, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
    }

    // Data Sources
    async listSources() {
        return this.request(API_ENDPOINTS.listSources, { method: 'GET' });
    }

    async addSource(sourceData) {
        return this.request(API_ENDPOINTS.addSource, {
            method: 'POST',
            body: JSON.stringify(sourceData)
        });
    }

    async updateSource(sourceId, sourceData) {
        return this.request(API_ENDPOINTS.updateSource(sourceId), {
            method: 'PUT',
            body: JSON.stringify(sourceData)
        });
    }

    async deleteSource(sourceId) {
        return this.request(API_ENDPOINTS.deleteSource(sourceId), {
            method: 'DELETE'
        });
    }

    async testSource(sourceId) {
        return this.request(API_ENDPOINTS.testSource(sourceId), {
            method: 'POST'
        });
    }

    // Notifications
    async getNotifications(limit = 20) {
        return this.request(`${API_ENDPOINTS.getNotifications}?limit=${limit}`, {
            method: 'GET'
        });
    }

    async getStats() {
        return this.request(API_ENDPOINTS.getStats, { method: 'GET' });
    }

    async getStatus() {
        return this.request(API_ENDPOINTS.getStatus, { method: 'GET' });
    }

    // Settings
    async getSettings() {
        return this.request(API_ENDPOINTS.getSettings, { method: 'GET' });
    }

    async updateSettings(settings) {
        return this.request(API_ENDPOINTS.updateSettings, {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
    }
}

// Initialize API client
const apiClient = new ApiClient();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
}

