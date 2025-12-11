// Authentication Management
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.token = null;
        this.loadUserFromStorage();
    }

    loadUserFromStorage() {
        const storedUser = localStorage.getItem('currentUser');
        const storedToken = localStorage.getItem('authToken');
        
        if (storedUser && storedToken) {
            this.currentUser = JSON.parse(storedUser);
            this.token = storedToken;
        }
    }

    async signup(email, password, phone = null) {
        try {
            const response = await fetch(getApiUrl(API_ENDPOINTS.signup), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email,
                    password,
                    phone
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Signup failed');
            }

            this.setUser(data.user, data.token);
            return data;
        } catch (error) {
            console.error('Signup error:', error);
            throw error;
        }
    }

    async login(email, password) {
        try {
            const response = await fetch(getApiUrl(API_ENDPOINTS.login), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email,
                    password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Login failed');
            }

            this.setUser(data.user, data.token);
            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    logout() {
        this.currentUser = null;
        this.token = null;
        localStorage.removeItem('currentUser');
        localStorage.removeItem('authToken');
        window.location.reload();
    }

    setUser(user, token) {
        this.currentUser = user;
        this.token = token;
        localStorage.setItem('currentUser', JSON.stringify(user));
        localStorage.setItem('authToken', token);
    }

    isAuthenticated() {
        return this.token !== null && this.currentUser !== null;
    }

    getAuthHeaders() {
        if (!this.token) {
            return {
                'Content-Type': 'application/json'
            };
        }

        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }

    async refreshToken() {
        try {
            const response = await fetch(getApiUrl(API_ENDPOINTS.refresh), {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            const data = await response.json();

            if (response.ok && data.token) {
                this.token = data.token;
                localStorage.setItem('authToken', data.token);
                return true;
            }

            return false;
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }
}

// Initialize auth manager
const authManager = new AuthManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuthManager;
}

