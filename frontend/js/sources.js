// Data Sources Management
class SourcesManager {
    constructor() {
        this.sources = [];
        this.modal = document.getElementById('addSourceModal');
        this.form = document.getElementById('addSourceForm');
    }

    async loadSources() {
        try {
            this.sources = await apiClient.listSources();
            this.renderSources();
        } catch (error) {
            console.error('Error loading sources:', error);
            showToast('Failed to load data sources', 'error');
            document.getElementById('sourcesList').innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading data sources</p>
                </div>
            `;
        }
    }

    renderSources() {
        const sourcesList = document.getElementById('sourcesList');
        
        if (!this.sources || this.sources.length === 0) {
            sourcesList.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-inbox"></i>
                    <p>No data sources configured</p>
                    <p style="margin-top: 1rem; color: var(--text-secondary);">
                        Click "Add Data Source" to get started
                    </p>
                </div>
            `;
            return;
        }

        sourcesList.innerHTML = this.sources.map(source => `
            <div class="source-card" data-source-id="${source.source_id}">
                <div class="source-info">
                    <div class="source-icon">
                        <i class="fas fa-envelope"></i>
                    </div>
                    <div class="source-details">
                        <h3>${this.escapeHtml(source.email || source.source_id)}</h3>
                        <p>
                            ${this.getSourceTypeLabel(source.source_type)} • 
                            ${this.getStatusBadge(source.status)} • 
                            Last sync: ${this.formatLastSync(source.last_sync_at)}
                        </p>
                    </div>
                </div>
                <div class="source-actions">
                    <button class="btn-icon" onclick="sourcesManager.testSource('${source.source_id}')" 
                            title="Test Connection">
                        <i class="fas fa-plug"></i>
                    </button>
                    <button class="btn-icon" onclick="sourcesManager.toggleSource('${source.source_id}')" 
                            title="${source.status === 'active' ? 'Pause' : 'Activate'}">
                        <i class="fas fa-${source.status === 'active' ? 'pause' : 'play'}"></i>
                    </button>
                    <button class="btn-icon danger" onclick="sourcesManager.deleteSource('${source.source_id}')" 
                            title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    getSourceTypeLabel(type) {
        const labels = {
            'email': 'Email (IMAP)',
            'linkedin': 'LinkedIn',
            'twitter': 'Twitter'
        };
        return labels[type] || type;
    }

    getStatusBadge(status) {
        const badges = {
            'active': '<span class="status-badge status-active"><i class="fas fa-circle"></i> Active</span>',
            'paused': '<span class="status-badge status-inactive"><i class="fas fa-circle"></i> Paused</span>',
            'error': '<span class="status-badge status-inactive"><i class="fas fa-circle"></i> Error</span>'
        };
        return badges[status] || status;
    }

    formatLastSync(lastSync) {
        if (!lastSync) return 'Never';
        const date = new Date(lastSync);
        return dashboard.formatRelativeTime(date);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    openAddModal() {
        this.modal.classList.add('active');
        this.form.reset();
    }

    closeAddModal() {
        this.modal.classList.remove('active');
    }

    async addSource(sourceData) {
        try {
            const newSource = await apiClient.addSource(sourceData);
            showToast('Data source added successfully', 'success');
            this.closeAddModal();
            await this.loadSources();
        } catch (error) {
            console.error('Error adding source:', error);
            showToast(error.message || 'Failed to add data source', 'error');
        }
    }

    async deleteSource(sourceId) {
        if (!confirm('Are you sure you want to delete this data source?')) {
            return;
        }

        try {
            await apiClient.deleteSource(sourceId);
            showToast('Data source deleted', 'success');
            await this.loadSources();
        } catch (error) {
            console.error('Error deleting source:', error);
            showToast(error.message || 'Failed to delete data source', 'error');
        }
    }

    async toggleSource(sourceId) {
        const source = this.sources.find(s => s.source_id === sourceId);
        if (!source) return;

        const newStatus = source.status === 'active' ? 'paused' : 'active';
        
        try {
            await apiClient.updateSource(sourceId, { status: newStatus });
            showToast(`Data source ${newStatus === 'active' ? 'activated' : 'paused'}`, 'success');
            await this.loadSources();
        } catch (error) {
            console.error('Error updating source:', error);
            showToast(error.message || 'Failed to update data source', 'error');
        }
    }

    async testSource(sourceId) {
        try {
            showToast('Testing connection...', 'warning');
            const result = await apiClient.testSource(sourceId);
            if (result.success) {
                showToast('Connection test successful!', 'success');
            } else {
                showToast(result.message || 'Connection test failed', 'error');
            }
        } catch (error) {
            console.error('Error testing source:', error);
            showToast(error.message || 'Connection test failed', 'error');
        }
    }
}

// Initialize sources manager
const sourcesManager = new SourcesManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SourcesManager;
}

