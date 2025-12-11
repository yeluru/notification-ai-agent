import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Bell, Mail, Settings, LogOut, Menu } from 'lucide-react'
import { useState } from 'react'
import './Layout.css'

function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const isActive = (path) => location.pathname === path

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-brand">
            <Bell className="nav-icon" />
            <span>Notification Agent</span>
          </div>
          
          <button 
            className="mobile-menu-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <Menu />
          </button>

          <div className={`nav-menu ${mobileMenuOpen ? 'open' : ''}`}>
            <Link
              to="/"
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <Bell /> Dashboard
            </Link>
            <Link
              to="/sources"
              className={`nav-link ${isActive('/sources') ? 'active' : ''}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <Mail /> Data Sources
            </Link>
            <Link
              to="/settings"
              className={`nav-link ${isActive('/settings') ? 'active' : ''}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <Settings /> Settings
            </Link>
            <div className="user-menu">
              <span className="user-email">{user?.email}</span>
              <button className="btn-logout" onClick={logout}>
                <LogOut /> Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout

