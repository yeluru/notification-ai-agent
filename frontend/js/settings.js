// Settings Management
class SettingsManager {
    constructor() {
        this.settings = null;
    }

    async loadSettings() {
        try {
            // Load user info
            const user = await apiClient.getUser();
            document.getElementById('accountEmail').textContent = user.email || '-';
            document.getElementById('accountPhone').textContent = user.phone || '-';
            
            if (user.created_at) {
                const createdDate = new Date(user.created_at);
                document.getElementById('accountCreated').textContent = createdDate.toLocaleDateString();
            }

            // Load notification settings
            const settings = await apiClient.getSettings();
            this.settings = settings;

            // Populate form
            if (settings.notification_method) {
                document.getElementById('notificationMethod').value = settings.notification_method;
            }
            if (settings.notification_email) {
                document.getElementById('notificationEmail').value = settings.notification_email;
            }
            if (settings.notification_phone) {
                document.getElementById('notificationPhone').value = settings.notification_phone;
            }
            if (settings.summary_frequency) {
                document.getElementById('summaryFrequency').value = settings.summary_frequency;
            }
        } catch (error) {
            console.error('Error loading settings:', error);
            showToast('Failed to load settings', 'error');
        }
    }

    async saveSettings() {
        const settings = {
            notification_method: document.getElementById('notificationMethod').value,
            notification_email: document.getElementById('notificationEmail').value,
            notification_phone: document.getElementById('notificationPhone').value,
            summary_frequency: parseInt(document.getElementById('summaryFrequency').value)
        };

        try {
            await apiClient.updateSettings(settings);
            showToast('Settings saved successfully', 'success');
            this.settings = settings;
        } catch (error) {
            console.error('Error saving settings:', error);
            showToast(error.message || 'Failed to save settings', 'error');
        }
    }
}

// Initialize settings manager
const settingsManager = new SettingsManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SettingsManager;
}

