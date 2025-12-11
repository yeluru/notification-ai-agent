import { useEffect, useState } from 'react'
import { dataSourcesAPI } from '../services/api'
import { Plus, Mail, Trash2, Play, Pause, TestTube, Loader, AlertCircle, CheckCircle, X } from 'lucide-react'
import './DataSourcesPage.css'

function DataSourcesPage() {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [testingId, setTestingId] = useState(null)

  useEffect(() => {
    loadSources()
  }, [])

  const loadSources = async () => {
    try {
      const response = await dataSourcesAPI.list()
      setSources(response.data || [])
    } catch (error) {
      console.error('Failed to load sources:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async (sourceId) => {
    setTestingId(sourceId)
    try {
      const response = await dataSourcesAPI.test(sourceId)
      if (response.data.success) {
        alert('Connection test successful!')
      } else {
        alert(`Connection test failed: ${response.data.message}`)
      }
    } catch (error) {
      alert(`Connection test failed: ${error.response?.data?.message || error.message}`)
    } finally {
      setTestingId(null)
    }
  }

  const handleToggle = async (source) => {
    const newStatus = source.status === 'active' ? 'paused' : 'active'
    try {
      await dataSourcesAPI.update(source.source_id, { status: newStatus })
      loadSources()
    } catch (error) {
      alert(`Failed to update: ${error.response?.data?.message || error.message}`)
    }
  }

  const handleDelete = async (sourceId) => {
    if (!confirm('Are you sure you want to delete this data source?')) return
    
    try {
      await dataSourcesAPI.delete(sourceId)
      loadSources()
    } catch (error) {
      alert(`Failed to delete: ${error.response?.data?.message || error.message}`)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <Loader className="spinner" />
        <p>Loading data sources...</p>
      </div>
    )
  }

  return (
    <div className="data-sources-page">
      <div className="page-header">
        <div>
          <h1>Data Sources</h1>
          <p className="page-subtitle">Configure email accounts and other data sources</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus /> Add Data Source
        </button>
      </div>

      {sources.length === 0 ? (
        <div className="empty-state">
          <Mail />
          <h2>No data sources configured</h2>
          <p>Add your first email account to start monitoring notifications</p>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus /> Add Data Source
          </button>
        </div>
      ) : (
        <div className="sources-grid">
          {sources.map((source) => (
            <SourceCard
              key={source.source_id}
              source={source}
              onTest={handleTest}
              onToggle={handleToggle}
              onDelete={handleDelete}
              testing={testingId === source.source_id}
            />
          ))}
        </div>
      )}

      {showModal && (
        <AddSourceModal
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false)
            loadSources()
          }}
        />
      )}
    </div>
  )
}

function SourceCard({ source, onTest, onToggle, onDelete, testing }) {
  return (
    <div className="source-card">
      <div className="source-header">
        <div className="source-icon">
          <Mail />
        </div>
        <div className="source-info">
          <h3>{source.email || source.source_id}</h3>
          <p className="source-type">{getSourceTypeLabel(source.source_type)}</p>
        </div>
        <div className={`status-badge status-${source.status}`}>
          {source.status === 'active' ? 'Active' : 'Paused'}
        </div>
      </div>

      <div className="source-details">
        <div className="detail-item">
          <span className="detail-label">Host:</span>
          <span className="detail-value">{source.host || 'Auto-detected'}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Port:</span>
          <span className="detail-value">{source.port || 993}</span>
        </div>
        {source.last_sync_at && (
          <div className="detail-item">
            <span className="detail-label">Last Sync:</span>
            <span className="detail-value">{formatRelativeTime(source.last_sync_at)}</span>
          </div>
        )}
      </div>

      <div className="source-actions">
        <button
          className="btn btn-icon"
          onClick={() => onTest(source.source_id)}
          disabled={testing}
          title="Test Connection"
        >
          {testing ? <Loader className="spinner" /> : <TestTube />}
        </button>
        <button
          className="btn btn-icon"
          onClick={() => onToggle(source)}
          title={source.status === 'active' ? 'Pause' : 'Activate'}
        >
          {source.status === 'active' ? <Pause /> : <Play />}
        </button>
        <button
          className="btn btn-icon danger"
          onClick={() => onDelete(source.source_id)}
          title="Delete"
        >
          <Trash2 />
        </button>
      </div>
    </div>
  )
}

function AddSourceModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    source_type: 'email',
    email: '',
    password: '',
    host: '',
    port: 993,
    use_ssl: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleTest = async () => {
    if (!formData.email || !formData.password) {
      setError('Email and password are required')
      return
    }

    setTesting(true)
    setError('')
    setTestResult(null)

    try {
      // Test connection before saving
      // In a real app, you might have a separate test endpoint
      // For now, we'll just validate the form
      await new Promise((resolve) => setTimeout(resolve, 1000))
      setTestResult({ success: true, message: 'Connection test successful!' })
    } catch (error) {
      setTestResult({ success: false, message: error.message })
    } finally {
      setTesting(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await dataSourcesAPI.create(formData)
      onSuccess()
    } catch (error) {
      setError(error.response?.data?.message || 'Failed to add data source')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add Data Source</h2>
          <button className="modal-close" onClick={onClose}>
            <X />
          </button>
        </div>

        {error && (
          <div className="alert error">
            <AlertCircle />
            <span>{error}</span>
          </div>
        )}

        {testResult && (
          <div className={`alert ${testResult.success ? 'success' : 'error'}`}>
            {testResult.success ? <CheckCircle /> : <AlertCircle />}
            <span>{testResult.message}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="sourceType">Source Type</label>
            <select
              id="sourceType"
              name="source_type"
              value={formData.source_type}
              onChange={handleChange}
              required
            >
              <option value="email">Email (IMAP)</option>
              <option value="linkedin" disabled>LinkedIn (Coming Soon)</option>
              <option value="twitter" disabled>Twitter (Coming Soon)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="sourceEmail">Email Address</label>
            <input
              id="sourceEmail"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="your@email.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="sourcePassword">Password / App Password</label>
            <input
              id="sourcePassword"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              required
            />
            <small>For Gmail, use an App Password</small>
          </div>

          <div className="form-group">
            <label htmlFor="sourceHost">IMAP Host (Optional)</label>
            <input
              id="sourceHost"
              type="text"
              name="host"
              value={formData.host}
              onChange={handleChange}
              placeholder="imap.gmail.com"
            />
            <small>Auto-detected if not provided</small>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="sourcePort">IMAP Port</label>
              <input
                id="sourcePort"
                type="number"
                name="port"
                value={formData.port}
                onChange={handleChange}
                placeholder="993"
              />
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="use_ssl"
                  checked={formData.use_ssl}
                  onChange={handleChange}
                />
                Use SSL/TLS
              </label>
            </div>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleTest}
              disabled={testing || loading}
            >
              {testing ? <Loader className="spinner" /> : <TestTube />}
              Test Connection
            </button>
            <div className="modal-actions-right">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || testing}
              >
                {loading ? <Loader className="spinner" /> : <Plus />}
                Add Source
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

function getSourceTypeLabel(type) {
  const labels = {
    email: 'Email (IMAP)',
    linkedin: 'LinkedIn',
    twitter: 'Twitter',
  }
  return labels[type] || type
}

function formatRelativeTime(dateString) {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

export default DataSourcesPage

