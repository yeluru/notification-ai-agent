import { useEffect, useState } from 'react'
import { userAPI, settingsAPI } from '../services/api'
import { Save, Bell, User, Loader, AlertCircle, CheckCircle } from 'lucide-react'
import './SettingsPage.css'

function SettingsPage() {
  const [user, setUser] = useState(null)
  const [settings, setSettings] = useState({
    notification_method: 'email',
    notification_email: '',
    notification_phone: '',
    summary_frequency: 15,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [userRes, settingsRes] = await Promise.all([
        userAPI.getProfile(),
        settingsAPI.get(),
      ])
      setUser(userRes.data)
      setSettings(settingsRes.data || settings)
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value, type } = e.target
    setSettings((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) : value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)

    try {
      await settingsAPI.update(settings)
      setMessage({ type: 'success', text: 'Settings saved successfully!' })
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.message || 'Failed to save settings',
      })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <Loader className="spinner" />
        <p>Loading settings...</p>
      </div>
    )
  }

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <p className="page-subtitle">Manage your notification preferences</p>
      </div>

      {message && (
        <div className={`alert ${message.type}`}>
          {message.type === 'success' ? <CheckCircle /> : <AlertCircle />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="settings-sections">
        <div className="settings-section">
          <div className="section-header">
            <Bell />
            <h2>Notification Preferences</h2>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="notificationMethod">Delivery Method</label>
              <select
                id="notificationMethod"
                name="notification_method"
                value={settings.notification_method}
                onChange={handleChange}
              >
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="both">Both</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="notificationEmail">Notification Email</label>
              <input
                id="notificationEmail"
                type="email"
                name="notification_email"
                value={settings.notification_email}
                onChange={handleChange}
                placeholder="notifications@example.com"
              />
            </div>

            <div className="form-group">
              <label htmlFor="notificationPhone">Notification Phone</label>
              <input
                id="notificationPhone"
                type="tel"
                name="notification_phone"
                value={settings.notification_phone}
                onChange={handleChange}
                placeholder="+1234567890"
              />
            </div>

            <div className="form-group">
              <label htmlFor="summaryFrequency">Summary Frequency</label>
              <select
                id="summaryFrequency"
                name="summary_frequency"
                value={settings.summary_frequency}
                onChange={handleChange}
              >
                <option value="10">Every 10 minutes</option>
                <option value="15">Every 15 minutes</option>
                <option value="30">Every 30 minutes</option>
                <option value="60">Every hour</option>
              </select>
            </div>

            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <Loader className="spinner" /> : <Save />}
              Save Settings
            </button>
          </form>
        </div>

        <div className="settings-section">
          <div className="section-header">
            <User />
            <h2>Account Information</h2>
          </div>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Email</span>
              <span className="info-value">{user?.email || '-'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Phone</span>
              <span className="info-value">{user?.phone || '-'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Account Created</span>
              <span className="info-value">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : '-'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage

