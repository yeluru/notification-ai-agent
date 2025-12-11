import { useEffect, useState } from 'react'
import { notificationsAPI } from '../services/api'
import { Mail, CheckCircle, Send, Clock, AlertCircle, Loader } from 'lucide-react'
import './DashboardPage.css'

function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [status, setStatus] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [statsRes, statusRes, notificationsRes] = await Promise.all([
        notificationsAPI.getStats(),
        notificationsAPI.getStatus(),
        notificationsAPI.list(10),
      ])
      setStats(statsRes.data)
      setStatus(statusRes.data)
      setNotifications(notificationsRes.data || [])
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <Loader className="spinner" />
        <p>Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p className="page-subtitle">Monitor your notification processing status</p>
      </div>

      <div className="stats-grid">
        <StatCard
          icon={<Mail />}
          value={stats?.total_emails || 0}
          label="Total Emails Processed"
          gradient="primary"
        />
        <StatCard
          icon={<CheckCircle />}
          value={stats?.active_sources || 0}
          label="Active Data Sources"
          gradient="secondary"
        />
        <StatCard
          icon={<Send />}
          value={stats?.notifications_sent || 0}
          label="Notifications Sent"
          gradient="accent"
        />
        <StatCard
          icon={<Clock />}
          value={formatRelativeTime(stats?.last_sync)}
          label="Last Sync"
          gradient="success"
        />
      </div>

      <div className="dashboard-sections">
        <div className="section">
          <h2>Recent Activity</h2>
          <div className="activity-list">
            {notifications.length === 0 ? (
              <div className="empty-state">
                <AlertCircle />
                <p>No recent activity</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <ActivityItem key={notification.notification_id} notification={notification} />
              ))
            )}
          </div>
        </div>

        <div className="section">
          <h2>System Status</h2>
          <div className="status-grid">
            <StatusItem
              label="Processing Status"
              value={status?.processing_active ? 'Active' : 'Inactive'}
              status={status?.processing_active ? 'active' : 'inactive'}
            />
            <StatusItem
              label="Next Run"
              value={formatRelativeTime(status?.next_run) || 'Not scheduled'}
            />
            <StatusItem
              label="LLM Service"
              value={status?.llm_connected ? 'Connected' : 'Disconnected'}
              status={status?.llm_connected ? 'active' : 'inactive'}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, value, label, gradient }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon gradient-${gradient}`}>{icon}</div>
      <div className="stat-content">
        <h3>{value}</h3>
        <p>{label}</p>
      </div>
    </div>
  )
}

function ActivityItem({ notification }) {
  return (
    <div className="activity-item">
      <div className="activity-icon">
        <Mail />
      </div>
      <div className="activity-content">
        <p>{notification.summary || notification.content || 'New notification'}</p>
        <small>{formatRelativeTime(notification.created_at)}</small>
      </div>
    </div>
  )
}

function StatusItem({ label, value, status }) {
  return (
    <div className="status-item">
      <span className="status-label">{label}</span>
      {status ? (
        <span className={`status-badge status-${status}`}>{value}</span>
      ) : (
        <span className="status-value">{value}</span>
      )}
    </div>
  )
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
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  
  return date.toLocaleDateString()
}

export default DashboardPage

