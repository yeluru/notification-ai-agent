// Dashboard functionality
class Dashboard {
    constructor() {
        this.statsInterval = null;
        this.activityInterval = null;
    }

    async loadDashboard() {
        await Promise.all([
            this.loadStats(),
            this.loadActivity(),
            this.loadStatus()
        ]);

        // Set up auto-refresh every 30 seconds
        this.statsInterval = setInterval(() => this.loadStats(), 30000);
        this.activityInterval = setInterval(() => this.loadActivity(), 30000);
    }

    async loadStats() {
        try {
            const stats = await apiClient.getStats();
            
            document.getElementById('totalEmails').textContent = stats.total_emails || 0;
            document.getElementById('activeSources').textContent = stats.active_sources || 0;
            document.getElementById('notificationsSent').textContent = stats.notifications_sent || 0;
            
            if (stats.last_sync) {
                const lastSync = new Date(stats.last_sync);
                document.getElementById('lastSync').textContent = this.formatRelativeTime(lastSync);
            } else {
                document.getElementById('lastSync').textContent = 'Never';
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            showToast('Failed to load statistics', 'error');
        }
    }

    async loadActivity() {
        try {
            const notifications = await apiClient.getNotifications(10);
            const activityList = document.getElementById('activityList');
            
            if (!notifications || notifications.length === 0) {
                activityList.innerHTML = `
                    <div class="activity-item">
                        <div class="activity-content">
                            <p>No recent activity</p>
                        </div>
                    </div>
                `;
                return;
            }

            activityList.innerHTML = notifications.map(notification => `
                <div class="activity-item">
                    <div class="activity-icon">
                        <i class="fas fa-envelope"></i>
                    </div>
                    <div class="activity-content">
                        <p>${this.escapeHtml(notification.summary || notification.content || 'New notification')}</p>
                        <small>${this.formatRelativeTime(new Date(notification.created_at))}</small>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading activity:', error);
            activityList.innerHTML = `
                <div class="activity-item">
                    <div class="activity-content">
                        <p>Error loading activity</p>
                    </div>
                </div>
            `;
        }
    }

    async loadStatus() {
        try {
            const status = await apiClient.getStatus();
            
            // Processing status
            const processingStatus = document.getElementById('processingStatus');
            if (status.processing_active) {
                processingStatus.className = 'status-badge status-active';
                processingStatus.innerHTML = '<i class="fas fa-circle"></i> Active';
            } else {
                processingStatus.className = 'status-badge status-inactive';
                processingStatus.innerHTML = '<i class="fas fa-circle"></i> Inactive';
            }

            // Next run
            if (status.next_run) {
                const nextRun = new Date(status.next_run);
                document.getElementById('nextRun').textContent = this.formatRelativeTime(nextRun);
            } else {
                document.getElementById('nextRun').textContent = 'Not scheduled';
            }

            // LLM status
            const llmStatus = document.getElementById('llmStatus');
            if (status.llm_connected) {
                llmStatus.className = 'status-badge status-active';
                llmStatus.innerHTML = '<i class="fas fa-circle"></i> Connected';
            } else {
                llmStatus.className = 'status-badge status-inactive';
                llmStatus.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
            }
        } catch (error) {
            console.error('Error loading status:', error);
        }
    }

    formatRelativeTime(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        
        return date.toLocaleDateString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    destroy() {
        if (this.statsInterval) {
            clearInterval(this.statsInterval);
        }
        if (this.activityInterval) {
            clearInterval(this.activityInterval);
        }
    }
}

// Initialize dashboard
const dashboard = new Dashboard();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Dashboard;
}

