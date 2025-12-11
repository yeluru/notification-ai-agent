// Main Application Controller
class App {
    constructor() {
        this.currentPage = 'login';
        this.init();
    }

    init() {
        // Check authentication
        if (authManager.isAuthenticated()) {
            this.showAuthenticatedUI();
        } else {
            this.showLoginPage();
        }

        // Set up event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                this.navigateToPage(page);
            });
        });

        // Login form
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleLogin();
        });

        // Signup form
        document.getElementById('signupForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleSignup();
        });

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => {
            authManager.logout();
        });

        // Signup/Login links
        document.getElementById('signupLink').addEventListener('click', (e) => {
            e.preventDefault();
            this.showSignupPage();
        });

        document.getElementById('loginLink').addEventListener('click', (e) => {
            e.preventDefault();
            this.showLoginPage();
        });

        // Add source button
        document.getElementById('addSourceBtn').addEventListener('click', () => {
            sourcesManager.openAddModal();
        });

        // Modal close
        document.getElementById('closeModalBtn').addEventListener('click', () => {
            sourcesManager.closeAddModal();
        });

        document.getElementById('cancelSourceBtn').addEventListener('click', () => {
            sourcesManager.closeAddModal();
        });

        // Add source form
        document.getElementById('addSourceForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleAddSource();
        });

        // Settings form
        document.getElementById('notificationSettingsForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await settingsManager.saveSettings();
        });

        // Close modal on outside click
        document.getElementById('addSourceModal').addEventListener('click', (e) => {
            if (e.target.id === 'addSourceModal') {
                sourcesManager.closeAddModal();
            }
        });
    }

    async handleLogin() {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            showToast('Logging in...', 'warning');
            await authManager.login(email, password);
            showToast('Login successful!', 'success');
            this.showAuthenticatedUI();
        } catch (error) {
            showToast(error.message || 'Login failed', 'error');
        }
    }

    async handleSignup() {
        const email = document.getElementById('signupEmail').value;
        const password = document.getElementById('signupPassword').value;
        const phone = document.getElementById('phone').value || null;

        try {
            showToast('Creating account...', 'warning');
            await authManager.signup(email, password, phone);
            showToast('Account created successfully!', 'success');
            this.showAuthenticatedUI();
        } catch (error) {
            showToast(error.message || 'Signup failed', 'error');
        }
    }

    async handleAddSource() {
        const formData = {
            source_type: document.getElementById('sourceType').value,
            email: document.getElementById('sourceEmail').value,
            password: document.getElementById('sourcePassword').value,
            host: document.getElementById('sourceHost').value || null,
            port: parseInt(document.getElementById('sourcePort').value) || 993,
            use_ssl: document.getElementById('sourceSSL').checked
        };

        await sourcesManager.addSource(formData);
    }

    showLoginPage() {
        this.hideAllPages();
        document.getElementById('loginPage').classList.add('active');
        this.currentPage = 'login';
    }

    showSignupPage() {
        this.hideAllPages();
        document.getElementById('signupPage').classList.add('active');
        this.currentPage = 'signup';
    }

    showAuthenticatedUI() {
        this.hideAllPages();
        document.querySelector('.navbar').style.display = 'block';
        this.navigateToPage('dashboard');
        
        // Update user email in navbar
        if (authManager.currentUser) {
            document.getElementById('userEmail').textContent = authManager.currentUser.email;
        }
    }

    navigateToPage(page) {
        this.hideAllPages();
        this.currentPage = page;

        // Update nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === page) {
                link.classList.add('active');
            }
        });

        // Show appropriate page
        const pageMap = {
            'dashboard': 'dashboardPage',
            'sources': 'sourcesPage',
            'settings': 'settingsPage'
        };

        const pageId = pageMap[page];
        if (pageId) {
            document.getElementById(pageId).classList.add('active');
            
            // Load page-specific data
            if (page === 'dashboard') {
                dashboard.loadDashboard();
            } else if (page === 'sources') {
                sourcesManager.loadSources();
            } else if (page === 'settings') {
                settingsManager.loadSettings();
            }
        }
    }

    hideAllPages() {
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
    }
}

// Toast notification utility
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle'
    };

    toast.innerHTML = `
        <i class="fas ${iconMap[type] || iconMap.success} toast-icon"></i>
        <div class="toast-message">${message}</div>
    `;

    container.appendChild(toast);

    // Remove toast after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 5000);
}

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new App();
    });
} else {
    new App();
}

