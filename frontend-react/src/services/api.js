import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refreshToken,
          })
          const { token } = response.data
          localStorage.setItem('authToken', token)
          // Retry original request
          error.config.headers.Authorization = `Bearer ${token}`
          return axios.request(error.config)
        } catch (refreshError) {
          // Refresh failed, logout
          localStorage.removeItem('authToken')
          localStorage.removeItem('refreshToken')
          window.location.href = '/login'
        }
      } else {
        // No refresh token, logout
        localStorage.removeItem('authToken')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  googleSignIn: (data) => api.post('/auth/google', data),
  logout: () => api.post('/auth/logout'),
  refresh: (refreshToken) => api.post('/auth/refresh', { refreshToken }),
}

// User API
export const userAPI = {
  getProfile: () => api.get('/users/me'),
  updateProfile: (data) => api.put('/users/me', data),
}

// Data Sources API
export const dataSourcesAPI = {
  list: () => api.get('/data-sources'),
  create: (data) => api.post('/data-sources', data),
  update: (id, data) => api.put(`/data-sources/${id}`, data),
  delete: (id) => api.delete(`/data-sources/${id}`),
  test: (id) => api.post(`/data-sources/${id}/test`),
}

// Notifications API
export const notificationsAPI = {
  list: (limit = 20) => api.get(`/notifications?limit=${limit}`),
  getStats: () => api.get('/stats'),
  getStatus: () => api.get('/status'),
}

// Settings API
export const settingsAPI = {
  get: () => api.get('/settings'),
  update: (data) => api.put('/settings', data),
}

export default api

